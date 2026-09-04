# Finality-Aware Planning v1.0.0

A planner for the decision FinalityBench poses: what to do when a payment
capture will not resolve before the order ships.

- **Prices the options** instead of escalating unconditionally. 91.9% exact
  against the strongest shipped policy's 85.4%, and $2.74 [1.80, 3.80] less
  mean position gap on a shared task resample.
- **Robust to the economics**: better in 27 of 27 cost settings.
- **The belief transfers**: fitted on the public split, holds on the
  regenerated one; a deliberately wrong prior is catastrophic.
- **A negative result about shields.** An expected-value shield is inert,
  because at this corpus's settle rate shipping blind pays. A downside
  criterion cuts premature irreversible actions from 66.0% to 7.0% and costs
  expected value to do it.

Two of the four components contribute nothing measurable, which the ablation
reports rather than hides. 81% of the margin comes from one archetype, which
makes the result depend on how the benchmark models an escalated case.

MIT licensed. Consumes FinalityBench v1.0.1.
