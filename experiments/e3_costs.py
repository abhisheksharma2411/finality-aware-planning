"""E3 -- does the planner's advantage survive moving the cost constants?

The planner beats the gate by refusing to escalate when escalation is not the
best-valued option. Whether it is depends on three numbers the benchmark
stipulates rather than measures: the dispute fee, the escalation cost, and the
cost of goods. If the advantage only exists at one setting, it is an artefact of
those numbers and not a result.

Both policies are re-measured at every setting, and the planner recomputes its
decision from whatever the constants are, which is the whole idea: it is not
tuned to a particular economy, it reads one.
"""

from __future__ import annotations

import itertools

from _common import banner, pair_map, provenance, save

from fap.belief import FinalityPrior
from fap.planner import FinalityAwarePlanner
from finalitybench import config
from finalitybench.bootstrap import mean_gap, paired_difference
from finalitybench.faults import FaultProfile
from finalitybench.policies import TransactionalRuntimePolicy
from finalitybench.runner import evaluate, summarize
from finalitybench.tasks import build_corpus
from finalitybench.world import EVAL_SEEDS

COGS_RATES = (0.40, 0.60, 0.80)
DISPUTE_COSTS = (1000, 2500, 5000)
ESCALATION_COSTS = (600, 1800, 3600)


def main() -> None:
    banner("E3 sensitivity to the cost constants")
    base = (config.COGS_RATE, config.DISPUTE_COST, config.ESCALATION_COST)
    rows = []
    try:
        for cogs, dispute, escalation in itertools.product(
                COGS_RATES, DISPUTE_COSTS, ESCALATION_COSTS):
            config.COGS_RATE, config.DISPUTE_COST, config.ESCALATION_COST = (
                cogs, dispute, escalation)
            corpus = build_corpus(n_tasks=320)
            prior = FinalityPrior.fit(corpus)
            policies = [TransactionalRuntimePolicy(), FinalityAwarePlanner(prior)]
            grades = evaluate(policies, corpus, profile=FaultProfile(), seeds=EVAL_SEEDS)
            by: dict[str, list] = {}
            for g in grades:
                by.setdefault(g.policy, []).append(g)
            d = paired_difference(by["planner"], by["transactional"], mean_gap,
                                  pair_of=pair_map(corpus), replicates=800)
            rows.append({
                "cogs_rate": cogs, "dispute_cost": dispute,
                "escalation_cost": escalation,
                "gate": summarize(grades, "transactional").mean_excess,
                "planner": summarize(grades, "planner").mean_excess,
                "difference": d.as_dict(),
                "planner_better": d.high < 0,
                "gate_better": d.low > 0,
            })
    finally:
        config.COGS_RATE, config.DISPUTE_COST, config.ESCALATION_COST = base

    better = sum(1 for r in rows if r["planner_better"])
    worse = sum(1 for r in rows if r["gate_better"])
    tie = len(rows) - better - worse

    save("e3_costs", {
        "provenance": provenance(experiment="e3_costs"),
        "grid": {"cogs_rates": list(COGS_RATES), "dispute_costs": list(DISPUTE_COSTS),
                 "escalation_costs": list(ESCALATION_COSTS)},
        "n_settings": len(rows), "planner_better": better,
        "gate_better": worse, "indistinguishable": tie, "rows": rows,
    })

    print(f"  {len(rows)} settings: planner better in {better}, "
          f"gate better in {worse}, indistinguishable in {tie}")
    print(f"\n  {'cogs':>6s}{'disp':>7s}{'esc':>7s}{'gate $':>10s}{'planner $':>11s}{'difference':>26s}")
    for r in rows:
        d = r["difference"]
        mark = "  planner" if r["planner_better"] else ("  gate" if r["gate_better"] else "  ns")
        print(f"  {r['cogs_rate']:6.2f}{r['dispute_cost']/100:7.0f}{r['escalation_cost']/100:7.0f}"
              f"{r['gate']/100:10.2f}{r['planner']/100:11.2f}"
              f"{d['point']/100:+8.2f} [{d['low']/100:+6.2f},{d['high']/100:+6.2f}]{mark}")


if __name__ == "__main__":
    main()
