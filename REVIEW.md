# Review

## Claim to evidence

| # | Claim | Evidence | Status |
|---|---|---|---|
| 1 | Planner beats the strongest baseline | E1 paired: −$2.74 [−3.80, −1.80]; `tests::test_planner_beats_the_gate_and_the_difference_excludes_zero` | measured |
| 2 | +6.5pp exact rate | E1 paired: [+4.1, +9.2] | measured |
| 3 | The advantage holds across the cost space | E3: 27/27, every interval below zero | measured, correlated settings |
| 4 | The fitted belief transfers | E4: −$2.67 on the regenerated split | measured |
| 5 | The fit is load-bearing | E4: wrong prior gives $201.22; `tests::test_a_wrong_prior_makes_the_planner_worse` | measured |
| 6 | The conditional prior matters | E2: +$11.45 to remove | measured |
| 7 | The decision rule is the main component | E2: +$18.30 to remove | measured |
| 8 | The shield is inert inside the planner | E2: $0.00 | measured, and structural |
| 9 | An EV shield cannot refuse a profitable gamble | E5: 0 blocks; `tests::test_expected_shield_permits_a_bet_that_pays` | measured |
| 10 | A downside shield cuts premature action 66.0%→7.0% | E5 | measured |
| 11 | 81% of the margin is one archetype | E1 by-archetype decomposition | measured |
| 12 | The planner never ships an unverified replacement | `tests::test_planner_never_ships_on_an_unverified_replacement` | measured |
| 13 | That a causal VoI rule would do better | — | **not claimed** |
| 14 | That any of this holds for stochastic agents | — | **not claimed** |

## Red-team

**"A payment-themed POMDP."** The specification's own warning, and the right
question. The answer is that the paper reports a measured improvement over the
strongest baseline the benchmark ships, with an interval, across the cost space,
and on a corpus the belief was not fitted to. It is a nine per cent improvement,
which is small, and the paper says so in the abstract.

**"Two of four components do nothing, so it is not a planner."** Fair. The
working parts are a conditional probability and four closed forms. The paper's
discussion concedes this and the peer review pushes harder on it.

**"The win is an artefact of the escalation model."** Substantially true and now
stated: 81% of the margin comes from the archetype where the gate escalates, and
the benchmark's analyst does not re-attempt payments. A more capable analyst
would shrink the margin.

## Readiness

**Release the artifact: yes.** Complete, tested, reproducible.

**Submit: as a short paper.** Six pages, one clear positive result of modest
size and one clean negative result about shields. cs.AI primary, cross-list
cs.LG.

**The caveat.** A reviewer who expects a planning paper to contain planning will
find a decision rule. The honest framing is that the environment does not need
more than that, which is itself worth knowing.
