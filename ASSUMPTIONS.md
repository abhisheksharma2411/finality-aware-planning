# Assumptions

1. **The prior is fitted on the public split.** That is the split the benchmark
   publishes for the purpose. E4 evaluates on the regenerated split, and the
   difference between the two is within noise.

2. **The settle rate is conditioned on survival time, not marginal.** Captures
   that resolve late are not a random sample; the marginal rate would tell the
   planner to ship exactly the cases that are a coin flip. The ablation prices
   the mistake at $11.45.

3. **The analyst model is inherited from the benchmark**, including the delay
   before an escalated case is picked up. The escalation term in the valuation
   is derived from it rather than chosen.

4. **The shield's downside criterion uses the worst branch, not a quantile.**
   With two outcomes there is no meaningful quantile to take; with a richer
   outcome space a CVaR would be the natural generalisation and is untested.

5. **A blocked action becomes a probe, not a veto.** Vetoing was measured first
   and turns a policy that gambles into one that never acts, which is not an
   improvement. This is a design choice and it favours the shield.

6. **The planner's own probing schedule matches the gate's** so that the
   comparison isolates the terminal decision. A planner free to choose its own
   schedule might do better or worse; that is untested.

7. **Cost sensitivity sweeps three constants over 27 combinations**, rebuilding
   and refitting at each. It does not test whether the four-term model of the
   merchant's position is the right model.
