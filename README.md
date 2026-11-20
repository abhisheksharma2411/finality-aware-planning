# Finality-Aware Planning

**When a payment capture will not resolve before the order ships, what should an
agent do?**

The strongest policy in [FinalityBench](https://github.com/abhisheksharma2411/finalitybench)
escalates the case to a human. That is safe, and on that corpus it is never the
best available action — escalation costs a flat fee on every case while the
alternatives cost something that depends on the order.

This is a planner that prices the options instead.

```
at the deadline, outcome still unknown, settle probability p:

  ship      pA − cogs        collect the order, or lose the goods
  close     −pD              a dispute whenever money arrives for an unfilled order
  escalate  −E − D·Pr[late]  a flat fee, and the dispute it does not avoid
  refund    −(1−p)A          return money that may never have come

  take the largest
```

Below roughly $125 of order value the gamble is cheap enough to take. Above it,
closing bounds the loss at half a dispute fee. Escalating is never the maximum.
The planner computes this rather than being told it, so it follows when the
costs change.

## Results

| policy | exact | mean gap | pass all 5 seeds |
|---|---:|---:|---:|
| ReAct loop | 54.0% | $128.19 | 17.4% |
| finality gate | 85.4% | $31.37 | 85.4% |
| **planner** | **91.9%** | **$28.63** | **91.9%** |

On a resample giving both policies the same tasks, the planner's mean gap is
**$2.74 [1.80, 3.80] lower** than the gate's — an interval excluding zero. It
holds in **27 of 27** settings of the three cost constants, and transfers to a
corpus the belief was not fitted to.

## Two findings worth the space

**Half the method is inert.** Removing the safety shield costs $0.00. Removing
the value-of-information rule costs $0.00. The working parts are a conditional
probability and a comparison of four expressions.

**An expected-value shield cannot refuse a profitable gamble.** Goods cost 60%
of the order and captures settle 72% of the time, so shipping without checking
has positive expected value. Only a criterion that asks what happens in the
branch it cannot rule out objects — and doing so cuts a ship-on-first-sign
policy's premature irreversible actions from **66.0% to 7.0%**, while making it
worse on the corpus's own outcome distribution. Which you want is a question
about risk preference, not about correctness.

## Quick start

```bash
make setup        # virtualenv; fetches FinalityBench if no sibling checkout
make test         # 14 tests
make experiments  # E1-E5
make paper        # figures, tables, PDF
make reproduce    # all of it, from a clean tree
```

## Using it

```python
from fap.belief import FinalityPrior
from fap.planner import FinalityAwarePlanner, Shielded
from finalitybench.policies import OptimisticPolicy

prior = FinalityPrior.fit()            # from the public split
planner = FinalityAwarePlanner(prior)  # a drop-in FinalityBench policy

guarded = Shielded(OptimisticPolicy(), prior)   # wrap any policy
guarded._shield.criterion = "downside"          # or "expected"
```

## Layout

| path | what |
|---|---|
| `src/fap/belief.py` | prior over resolution time, conditioned on what probes ruled out |
| `src/fap/planner.py` | the valuation, the planner, the shield and its wrapper |
| `experiments/` | E1–E5 |

## Documents

- [NOVELTY.md](NOVELTY.md) — what is new, against verified prior work
- [EXPERIMENTS.md](EXPERIMENTS.md) — every iteration, including the ones that failed
- [ASSUMPTIONS.md](ASSUMPTIONS.md) — choices made without asking
- [BLOCKERS.md](BLOCKERS.md) — what could not be done
- [PEER_REVIEW.md](PEER_REVIEW.md) — adversarial review and its resolution
- [REVIEW.md](REVIEW.md) — claim-to-evidence matrix

MIT licensed. Consumes FinalityBench at revision `0b01661`, which
`make setup` fetches; P1's tagged releases do not carry every module this
paper imports.
