# Experiment log

Every iteration, including the ones that came back wrong.

## Round 1 — the planner was worse than the baseline

**Ran.** First complete planner against the finality gate on the full corpus.

**Result.** Planner mean gap $78.65 against the gate's $31.37, and paired loss
$280.51 against $103.91. Worse on every measure.

**Diagnosis.** Per-archetype decomposition showed the planner beating the gate
on `unresolvable` (−$18.87) and `pending_fail` (−$15.96) exactly as designed,
and losing **$640.31 per case** on `pending_fail_hard`. The planner submitted a
replacement capture after a failure and then shipped without checking whether
the replacement settled. On unrecoverable failures the goods left and no money
arrived.

**Change.** Verify the replacement before shipping. This is the premature action
the benchmark is built to detect, committed by a policy written to avoid it.

**After.** Planner 91.9% exact and $28.63 mean gap, better than the gate on
every archetype where either loses.

## Round 2 — the significance test

Marginal intervals: planner $28.63 [14.22, 44.96], gate $31.37 [16.41, 48.27].
They overlap almost entirely and say nothing.

On a resample giving both policies the same tasks: mean gap −$2.74 [−3.80,
−1.80], exact rate +6.5pp [+4.1, +9.2]. Both exclude zero. The paired comparison
is the evidence; the marginal one is not.

## Round 3 — two of four components do nothing

| variant | cost of removal |
|---|---|
| no shield | **$0.00** |
| no value-of-information | **$0.00** |
| marginal instead of conditional prior | +$11.45 |
| fixed escalate rule | +$18.30 |

**Diagnosis of the shield.** It blocks irreversible actions whose expected value
falls below the best reversible alternative. The planner already selects the
maximum-value action, so the rule can never fire. It is the same rule stated
twice.

## Round 4 — the shield, moved somewhere it could matter

**Ran.** The shield as a wrapper around four policies that do not maximise
expected value.

**Result, expected-value criterion.** Zero blocks on three of four policies, and
no change in any outcome.

**Diagnosis.** Goods cost 60% of the order and captures settle 72% of the time,
so shipping without checking is worth +0.12A in expectation. A criterion built
on the mean cannot object to a bet that pays. This is the paper's most useful
finding and it arrived from an ablation that showed a component was useless.

**Result, downside criterion, first attempt.** Blocked essentially every ship
and collapsed the optimistic policy from 65.7% exact to 19.9%.

**Change.** When the shield objects, ask the agent to probe rather than
forbidding it to act. A veto turns a gambler into a policy that never moves.

**After.** Premature irreversible actions 66.0% → 7.0%, paired loss $253.53 →
$192.20, mean gap $163.61 → $244.29. It buys safety with expected value.

## Round 5 — robustness

**Cost sweep.** 27 combinations of cost of goods, dispute fee and escalation
cost, rebuilding and refitting at each. Planner better in 27, every interval
below zero. These are correlated re-measurements rather than independent tests,
which the paper now says.

**Transfer.** Prior fitted on the public split, evaluated on the regenerated
one: −$2.67 [−3.67, −1.75] against −$2.74 on the public split. A deliberately
wrong prior raises the planner's mean gap to $201.22.

## Round 6 — peer review

An adversarial pass found that 81% of the margin comes from `unresolvable`,
which makes the result depend on how the benchmark models an escalated case and
not only on what escalation costs. Recorded in the limitations. See
[PEER_REVIEW.md](PEER_REVIEW.md).

## Reproduction

`make reproduce` runs from a clean tree: FinalityBench resolved, 14 tests, five
experiments, three figures, six tables, and the paper.
