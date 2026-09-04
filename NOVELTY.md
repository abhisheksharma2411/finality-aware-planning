# Novelty

Every paper below was fetched and its authors, date and scope checked.

## The claim

We are not aware of prior work that prices the dispositions available to an
agent under unresolved payment finality and shows that a fixed escalation rule
is dominated by the valuation across the cost space.

We do not claim to have invented planning under partial observability, value of
information, or safety shields. Each is prior work and each is cited. The
contribution is the application and two measured results, one of them negative.

## Against the closest work

**Agentic Abstention** (arXiv:2606.28733, Luo, Wen, Wang, Jun 2026) treats
abstention as a sequential decision where an agent may answer, abstain or gather
more information, and finds agents struggle when a task looks feasible until the
environment says otherwise. That is this setting. The difference is that
abstention there is free, while escalation here is priced and competes with the
alternatives. The competition is what this paper is about.

**ShieldAgent** (arXiv:2503.22738, Chen, Kang, Li, Mar 2025) enforces safety
policies by extracting verifiable rules from policy documents and checking
compliance. That is a rule criterion: an action is blocked because it violates a
stated policy. Ours is a value criterion. Our negative result suggests the rule
approach may be the sounder one: a value shield must choose a functional of the
outcome distribution, and the obvious choice, the mean, cannot object to a bet
that pays.

**Leveraging the Value of Information in POMDP Planning** (arXiv:2604.01434,
Laouar, Ho, Sunberg, Apr 2026) skips observation branches in Monte Carlo tree
search where the value of information is low. Our probing rule is the same idea
at a much smaller scale, and we report that at this scale it is worth nothing.

**Scores Are Not Decisions** (arXiv:2607.27083, Feng, Zhang, Cheng, Qi, Jul
2026) proves score-only stopping rules are suboptimal under heterogeneous tool
costs. The same argument applies to our deadline decision, where the
alternatives have different costs and a rule that ignores them is dominated.

**Verified Tool Calls** (arXiv:2608.02645, Mansoor, Phadke, Rana, Jul 2026)
supplies the mechanisms our baseline implements. It is a strong baseline, which
is why the margin over it is small.

**Revisable by Design** (arXiv:2604.23283, Zhai, Li, Wang, Apr 2026) shows an
agent's flexibility is bounded by its reversibility. Our valuation is one way of
pricing that bound.

## What is modest

The margin over the strongest baseline is nine per cent, and 81% of it comes
from a single archetype whose economics depend on how the benchmark models an
escalation. Two of the four components contribute nothing measurable.

The more transferable finding is the negative one about shields, and it is
narrow too: established only against deterministic policies, in one environment,
with a two-outcome space where "downside" has an unambiguous meaning.
