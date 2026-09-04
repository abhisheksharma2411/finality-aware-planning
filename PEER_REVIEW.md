# Peer review — Finality-Aware Planning

Adversarial review run 2026-09-03 before release, per the standing rule that a
self-authored `REVIEW.md` does not count. Claims re-derived from the result
files rather than read from the prose.

**Recommendation: accept as a short paper; major revision if submitted as a full
one.** The result is real and carefully measured. It is also small, and it rests
on a modelling choice inherited from the benchmark that the paper did not
originally examine.

---

## Major

### 1. The margin depends on the benchmark's escalation *model*, not only its cost

The paper defends its result against the cost constants with a 27-setting sweep,
and that sweep is convincing as far as it goes. It varies the *price* of
escalation. It does not vary what escalation *does*.

Decomposing the margin by archetype: of the $2.74 total, **$2.23 (81%) comes
from `unresolvable`**, the archetype where the gate escalates and the planner
does not. FinalityBench models an escalated case as an analyst who completes the
disposition of money already held and does not start new money movement. Under
that model escalation is worth little, so declining to escalate is worth
something. An analyst who also re-attempted failed captures would make
escalation considerably more valuable and could erase the margin entirely.

This is not a flaw in the experiment; it is a dependency the paper should state
where a reader will see it. **Added to the limitations.**

### 2. The 27 cost settings are not 27 independent tests

Every setting reuses the same corpus generator, the same five fault seeds and
the same task draw. They are 27 correlated re-measurements, and reporting
"27 of 27" invites reading them as independent confirmations. The honest claim
is that the sign of the effect is stable across the region of cost space
examined, which is weaker and still worth stating.

### 3. Two of four components are inert, and the paper is a planner in name

Removing the shield costs $0.00 and removing the value-of-information rule costs
$0.00. What remains is a conditional probability and a comparison of four closed
forms evaluated once per episode. Calling that a planner oversells it. The paper
says so in the discussion, which is the right instinct, but the title and
framing do not.

---

## Moderate

### 4. The effect size deserves to be stated in the abstract in relative terms

$2.74 against a baseline of $31.37 is a 9% reduction. The abstract gives the
absolute figure and the interval, both correct, and a reader skimming will not
learn how small it is until the limitations.

### 5. The shield result is the more interesting contribution and is third

That an expected-value shield cannot refuse a profitable gamble, and that only a
downside criterion will, is a cleaner and more transferable finding than the
planner's margin. It arrives in Section VI-F.

### 6. `pass^k` is inherited, not contributed

The planner's reliability under repetition comes from deciding on the
authoritative channel, which is the gate's design. The paper says this. It is
worth keeping prominent so the number is not read as evidence for the planner.

---

## Minor

- The valuation assumes the four dispositions are exhaustive. Partial refunds,
  or shipping with a hold on the goods, are not modelled and might dominate.
- The downside criterion uses the worst branch because there are only two. With
  a richer outcome space it should be a CVaR, and the paper should say which
  generalisation it intends.
- "Deliberately wrong prior" is a weak control: it is wrong in a specific
  direction. A prior perturbed in several directions would bound the sensitivity
  better.

## What holds up

The paired resample is the right comparison and the paper is explicit about why
the marginal intervals are not. The premature-shipping bug the planner itself
committed is reported rather than quietly fixed, and it is genuine evidence that
the benchmark detects what it claims to. The transfer experiment uses the
regenerated split as intended, and the wrong-prior control shows the fitted
belief is load-bearing.
