"""Locate FinalityBench (P1), which this paper consumes rather than rebuilds.

FinalityAwarePlanning is a causal layer *over* FinalityBench: its environment, fault
engine, policies and effect-level oracle are the object of study, not something
reimplemented here.  Resolution order:

1. an installed ``finalitybench`` package;
2. a sibling checkout at ``../finalitybench/src`` (the usual local layout);
3. a clone under ``vendor/finalitybench`` that ``make setup`` creates.

Failing all three we raise with the exact command to fix it, rather than
falling back to a stand-in.  A stand-in would silently change what the paper is
about: the whole claim is that these results are computed against the published
P1 artifact.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P1_REPO = "https://github.com/abhisheksharma2411/finalitybench.git"

#: The exact FinalityBench revision these results were computed against.
#:
#: Not a tag. ``make setup`` used to clone tag v1.0.0, and this paper imports
#: ``finalitybench.bootstrap`` -- the module every confidence interval comes
#: from -- which exists in NEITHER v1.0.0 nor v1.0.1; it was added to P1's main
#: afterwards. So a clean machine cloned a release that cannot satisfy the
#: import, and `make reproduce` only ever worked where an unreleased sibling
#: checkout happened to be lying around. Pinning the commit is what makes the
#: artifact statement true: it is immutable, public, and is exactly the
#: revision recorded in every results file's provenance.
P1_REVISION = "0b016616808b164df273f30f4d033c06690f9627"

#: Imported by this paper and absent from P1's releases. Checked explicitly so
#: a wrong checkout fails here, naming the cause, instead of as a
#: ModuleNotFoundError from inside an experiment.
P1_REQUIRED_MODULES = ("bootstrap", "runner", "policies", "tasks", "env")

_CANDIDATES = (
    ROOT.parent / "finalitybench" / "src",
    ROOT / "vendor" / "finalitybench" / "src",
)


def ensure_p1() -> Path:
    """Put FinalityBench on ``sys.path`` and return the source root used."""
    try:
        import finalitybench  # noqa: F401
        return Path(finalitybench.__file__).resolve().parent.parent
    except ImportError:
        pass

    for candidate in _CANDIDATES:
        if (candidate / "finalitybench" / "__init__.py").exists():
            _require_modules(candidate)
            sys.path.insert(0, str(candidate))
            return candidate

    raise ImportError(
        "FinalityBench (P1) not found. This paper is a causal layer over it and "
        "does not reimplement it. Fetch it with:\n"
        f"    git clone {P1_REPO} vendor/finalitybench\n"
        "or place a checkout beside this repository."
    )


def _require_modules(src_root: Path) -> None:
    """Fail with the reason, not with a puzzling ImportError later."""
    missing = [m for m in P1_REQUIRED_MODULES
               if not (src_root / "finalitybench" / f"{m}.py").exists()]
    if missing:
        raise ImportError(
            f"the FinalityBench checkout at {src_root} is missing "
            f"{', '.join('finalitybench.' + m for m in missing)}. "
            f"This paper needs revision {P1_REVISION[:7]}; P1's tagged releases "
            "do not carry every module it imports. Remove the checkout and let "
            "`make setup` fetch the pinned revision."
        )


def clone_p1(dest: Path | None = None) -> Path:
    """Clone P1 at the pinned revision.  Used by ``make setup``."""
    dest = dest or (ROOT / "vendor" / "finalitybench")
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "--quiet", str(dest)], check=True)
    subprocess.run(["git", "-C", str(dest), "remote", "add", "origin", P1_REPO],
                   check=True)
    # Fetching one commit keeps this as cheap as the old --depth 1 clone.
    subprocess.run(
        ["git", "-C", str(dest), "fetch", "--quiet", "--depth", "1",
         "origin", P1_REVISION],
        check=True,
    )
    subprocess.run(["git", "-C", str(dest), "checkout", "--quiet", "FETCH_HEAD"],
                   check=True)
    _require_modules(dest / "src")
    return dest


def p1_provenance() -> dict[str, str]:
    """Which P1 the numbers were produced against.  Printed with every result."""
    ensure_p1()
    import finalitybench

    source = Path(finalitybench.__file__).resolve().parents[2]
    revision = "unknown"
    try:
        out = subprocess.run(
            ["git", "-C", str(source), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        revision = out.stdout.strip() or "unknown"
    except Exception:
        pass
    # The absolute path is deliberately not recorded. It published the
    # author's local directory layout into every result file and told a reader
    # nothing: the version and the commit identify which P1 produced the
    # numbers, and where it happened to sit on one machine does not.
    if source.is_relative_to(ROOT):
        location = f"./{source.relative_to(ROOT)}"
    elif (ROOT / "vendor" / "finalitybench") in source.parents or source.name == "finalitybench":
        location = "sibling checkout"
    else:
        location = "installed package"
    return {
        "finalitybench_version": finalitybench.__version__,
        "finalitybench_location": location,
        "finalitybench_git": revision,
    }


def ensure_or_clone() -> Path:
    """Resolve P1, fetching the pinned revision if it is not here yet.

    This is what ``make setup`` calls. It exists because importing this module
    must NOT resolve P1: setup has to be able to import ``clone_p1`` *before*
    P1 exists, and a module-level ``ensure_p1()`` made that impossible. A
    fresh clone of v1.0.1 failed with "FinalityBench (P1) not found" while
    trying to import the very function that would have fetched it.
    """
    try:
        return ensure_p1()
    except ImportError:
        clone_p1()
        return ensure_p1()
