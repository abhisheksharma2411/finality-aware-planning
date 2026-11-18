# Finality-Aware Planning v1.0.1

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

## Changes since v1.0.0

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
