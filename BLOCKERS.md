# Blockers

## 1. No language model — unresolved

The planner and every policy it is compared against are deterministic
procedures. Shields in the literature exist to constrain stochastic agents, and
the negative result here (an expected-value shield is inert; a downside shield
is not) is established only against deterministic ones. A model endpoint was
available for the companion benchmark's model arm but the quota would not cover
a policy that runs to forty steps across five seeds and twenty-seven cost
settings, so this arm was not attempted rather than attempted badly.

## 2. The causal value-of-information rule was not built

The scope called for deriving the value of an observation from causal
attribution over the same benchmark's traces, which identifies which messages
actually changed an outcome. What is implemented estimates the probability that
anything has resolved since the last look. That is cruder, and it is worth
nothing on this environment. The negative result reported is about the rule that
was built, not the one that was planned, and the paper says so.

## 3. Zenodo deposit — deferred

No Zenodo token. `scripts/insert_doi.py` fills the placeholder once a deposit
exists. Note that the GitHub–Zenodo webhook did not list newly created
repositories on this account even after a sync, so a manual deposit is the
reliable route.

## Not blockers

FinalityBench was available as a sibling checkout and is consumed rather than
reimplemented; `make setup` clones the released tag when no sibling is present.
LaTeX was available and the paper builds with zero undefined references.
