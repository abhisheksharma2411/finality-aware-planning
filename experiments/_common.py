"""Shared plumbing for the experiment scripts."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)


#: Paths that are outputs of a run rather than inputs to it. A run writes its
#: own results, and on the second experiment of a batch the first one's output
#: would otherwise make the tree look dirty and mark every later result as
#: irreproducible. What has to be clean is the code and the data that went in.
GENERATED = ("results/", "figures/", "paper/")


def _dirty_inputs(root) -> str:
    """Uncommitted changes outside the generated directories."""
    out = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"],
        capture_output=True, text=True, timeout=10,
    ).stdout.splitlines()
    changed = []
    for line in out:
        path = line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ")[-1]
        if not any(path.startswith(g) for g in GENERATED):
            changed.append(path)
    return "; ".join(sorted(changed))


def git_revision() -> dict[str, str]:
    """Full commit SHA and whether the tree was dirty.

    The short form was used at first and every result file recorded
    ``unversioned``, because the experiments ran before the repository had a
    first commit. A reader could not map a result to a revision, which is the
    only reason to record one.
    """
    info = {"commit": "uncommitted", "dirty": "unknown"}
    try:
        head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                              capture_output=True, text=True, timeout=5)
        if head.returncode == 0 and head.stdout.strip():
            info["commit"] = head.stdout.strip()
        info["dirty"] = "yes" if _dirty_inputs(ROOT) else "no"
    except Exception:
        pass
    return info


def provenance(**extra: Any) -> dict[str, Any]:
    from fap import __version__, p1_provenance

    revision = git_revision()
    return {"version": __version__,
            "git_commit": revision["commit"], "git_dirty": revision["dirty"],
            "command": " ".join(sys.argv),
            "python": platform.python_version(),
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            **p1_provenance(), **extra}


def save(name: str, payload: dict[str, Any]) -> Path:
    path = RESULTS / f"{name}.json"
    path.write_text(json.dumps(payload, indent=1))
    print(f"  wrote {path.relative_to(ROOT)}")
    return path


def load(name: str) -> dict[str, Any]:
    return json.loads((RESULTS / f"{name}.json").read_text())


def banner(title: str) -> None:
    print(f"\n=== {title} ===")


#: Baselines the planner is measured against. The finality gate is the one that
#: matters: it is the strongest policy the benchmark ships, and a planner that
#: does not beat it has no reason to exist.
BASELINES = ("rule_based", "react", "reflection", "transactional")


def baseline_policies():
    from finalitybench import policies as P

    return [P.RuleBasedPolicy(), P.ReActPolicy(), P.ReflectionPolicy(),
            P.TransactionalRuntimePolicy()]


def pair_map(corpus):
    """Twin pairs resample as one unit; they are two views of one construction."""
    out = {}
    for a, b in corpus.twin_pairs:
        out[a.task_id] = a.task_id
        out[b.task_id] = a.task_id
    return out
