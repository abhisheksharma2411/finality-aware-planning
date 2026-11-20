"""`make setup` must work on a machine that has never seen FinalityBench.

v1.0.1 shipped with ``ensure_p1()`` called at the bottom of ``fap/_p1.py``, so
importing that module resolved P1 as a side effect. ``make setup`` imports
``clone_p1`` from it -- the function whose entire job is to fetch P1 -- and so
could not run without P1 already present. A fresh clone died with
"FinalityBench (P1) not found" while importing the thing that would have fixed
it, and the Makefile hid the traceback behind ``2>/dev/null``.

The tests here recreate the three conditions a fresh clone has: no sibling
checkout, no installed package, no ``vendor/finalitybench``. Everything runs in
a subprocess under a copied source tree in a temp directory, because this test
suite itself imports modules that resolve P1, so an in-process check would pass
on a leak.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
PINNED = "0b016616808b164df273f30f4d033c06690f9627"


def _isolated_project(tmp_path: Path) -> Path:
    """A copy of the package under a root with no FinalityBench anywhere near.

    The real repo sits beside ``../finalitybench``, which ``_CANDIDATES``
    looks for. Copying under ``tmp_path/project`` means the parent directory
    holds nothing, so that candidate cannot resolve.
    """
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    shutil.copytree(REPO / "src" / "fap", project / "src" / "fap",
                    ignore=shutil.ignore_patterns("__pycache__"))
    assert not (project.parent / "finalitybench").exists()
    assert not (project / "vendor").exists()
    return project


def _run(project: Path, body: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items()
           if k not in ("PYTHONPATH", "PYTHONHOME")}
    script = textwrap.dedent(f"""
        import sys
        sys.path.insert(0, {str(project / "src")!r})
        {textwrap.indent(textwrap.dedent(body), " " * 8).lstrip()}
    """)
    return subprocess.run([sys.executable, "-c", script], cwd=project,
                          capture_output=True, text=True, env=env, timeout=300)


def test_isolation_is_real(tmp_path):
    """Control: without it, the regression test below could pass vacuously."""
    project = _isolated_project(tmp_path)
    out = _run(project, """
        import importlib.util
        assert importlib.util.find_spec("finalitybench") is None, "P1 leaked in"
        from fap._p1 import ensure_p1
        try:
            ensure_p1()
        except ImportError:
            print("ISOLATED")
        else:
            raise AssertionError("P1 resolved in an environment that has none")
    """)
    assert "ISOLATED" in out.stdout, out.stderr


def test_importing_p1_does_not_resolve_p1(tmp_path):
    """The regression: setup must be able to import the fetcher."""
    project = _isolated_project(tmp_path)
    out = _run(project, """
        from fap._p1 import ensure_or_clone, clone_p1, p1_provenance
        print("IMPORT OK")
    """)
    assert out.returncode == 0, out.stderr
    assert "IMPORT OK" in out.stdout


def test_importing_the_package_does_not_resolve_p1(tmp_path):
    """``import fap`` is what the Makefile triggers first."""
    project = _isolated_project(tmp_path)
    out = _run(project, """
        import fap
        print("PACKAGE OK", fap.__version__)
    """)
    assert out.returncode == 0, out.stderr
    assert "PACKAGE OK" in out.stdout


def test_setup_fetches_the_pinned_revision(tmp_path):
    """End to end: what ``make setup`` does, with nothing to start from."""
    project = _isolated_project(tmp_path)
    out = _run(project, f"""
        import subprocess
        from pathlib import Path
        from fap._p1 import ensure_or_clone, P1_REVISION
        assert P1_REVISION == {PINNED!r}
        src = ensure_or_clone()
        vendor = Path({str(project)!r}) / "vendor" / "finalitybench"
        assert vendor.exists(), "setup did not vendor P1"
        head = subprocess.run(["git", "-C", str(vendor), "rev-parse", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
        assert head == {PINNED!r}, f"fetched {{head}}, not the pin"
        import finalitybench
        from finalitybench.bootstrap import mean_gap, paired_difference
        from finalitybench.runner import evaluate
        print("SETUP OK", src)
    """)
    if out.returncode != 0 and (
        "Could not resolve host" in out.stderr or "unable to access" in out.stderr
    ):
        pytest.skip("no network available to fetch the pinned P1 revision")
    assert out.returncode == 0, out.stderr
    assert "SETUP OK" in out.stdout
