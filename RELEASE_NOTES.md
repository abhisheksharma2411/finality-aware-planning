# Finality-Aware Planning v1.0.2

A deadline decision rule for the choice FinalityBench poses: what to do when a
payment capture will not resolve before the order ships. It is not a sequential
planner -- a conditional probability and one comparison of four closed-form
expressions, evaluated once, with no search over action sequences and no
language model in the loop.

- **Prices the options** instead of escalating unconditionally. 91.9% exact
  against the strongest shipped policy's 85.4%, and $2.74 [1.80, 3.80] less
  mean position gap on a shared task resample.
- **Robust to the economics**: better in 27 of 27 cost settings, every
  interval below zero.
- **The belief transfers**: fitted on the public split, holds on the
  regenerated one; a deliberately wrong prior is catastrophic.
- **A negative result about shields.** An expected-value shield is inert,
  because at this corpus's settle rate shipping blind pays. A downside
  criterion cuts premature irreversible actions from 66.0% to 7.0% and costs
  expected value to do it.

Two of the four components contribute nothing measurable, which the ablation
reports rather than hides. 81% of the margin comes from one archetype, which
makes the result depend on how the benchmark models an escalated case; the
escalation sweep measures that and the margin survives it, shrinking from
$2.74 to $0.89 without changing sign.

## Changes since v1.0.1

- **`make setup` works on a machine that has never seen FinalityBench.** v1.0.1
  called `ensure_p1()` at the bottom of `fap/_p1.py`, so importing that module
  resolved P1 as a side effect. `make setup` imports `clone_p1` from it -- the
  function whose entire job is to fetch P1 -- so a fresh clone died with
  `ImportError: FinalityBench (P1) not found` while importing the thing that
  would have fetched it. The Makefile hid the traceback behind `2>/dev/null`
  and fell through to a fallback that failed the same way, so the error said
  nothing useful. Resolution now happens in `ensure_or_clone()`, which setup
  calls explicitly; the runtime modules that genuinely need P1 keep their own
  `ensure_p1()` calls.
- Added `tests/test_setup_isolation.py`, which runs setup under a copied source
  tree in a temp directory with no sibling checkout, no installed package and
  no `vendor/finalitybench`, and includes a control asserting the isolation is
  real so the regression test cannot pass vacuously.
- The artifact statement carries the archival DOI, `10.5281/zenodo.24406794`.
- README no longer claims the paper consumes FinalityBench v1.0.1; it names the
  revision, as RELEASE_NOTES already did.

## Changes in v1.0.1

- **`make setup` now fetches the FinalityBench revision these results were
  actually computed against** (`0b01661`), instead of cloning tag v1.0.0. This
  paper imports `finalitybench.bootstrap`, the module every confidence
  interval comes from, and that module exists in neither v1.0.0 nor v1.0.1 --
  it was added to P1's main afterwards. So `make reproduce` previously
  succeeded only on a machine that already had an unreleased sibling checkout,
  and failed at import anywhere else. A wrong checkout now fails immediately,
  naming the missing modules.
- Corrected the evaluation-size wording. 8,025 is every policy's episodes
  added together: 321 tasks x 5 fault schedules = 1,605 per policy, x 5
  policies compared = 8,025. The rule's 91.9% is over its own 1,605.
- Report paired contrasts as reductions, with the interval negated, so an
  improvement is no longer printed as a negative number.
- Table I spans both columns; it had been overprinting the adjacent column and
  losing its last data column off the page.
- Boxed the DOIs in the references, one of which was being hyphenated into a
  dead identifier.
- Tied archetype rows sort by name, so regeneration is deterministic.
- Added related work on pricing escalation and on post-hoc payment accounting.

Counts: 6 pages, 4 figures, 7 tables. MIT licensed.
