"""E1 -- does the planner beat the strongest policy the benchmark ships?

The finality gate escalates every case whose outcome it cannot establish before
the ship-by deadline. The planner values the alternatives instead. Everything
else the two do is the same, so the difference isolates that one decision.

Reported as a paired difference on a shared task resample, because the marginal
intervals for the two policies overlap almost entirely and comparing them would
say nothing. The two policies face identical tasks; the comparison should use
that.
"""

from __future__ import annotations

from _common import baseline_policies, banner, pair_map, provenance, save

from fap.belief import FinalityPrior
from fap.planner import FinalityAwarePlanner
from finalitybench.bootstrap import (
    bootstrap,
    exact_rate,
    mean_gap,
    paired_difference,
    pass_all_seeds,
    premature_rate,
)
from finalitybench.faults import FaultProfile
from finalitybench.runner import by_archetype, evaluate, paired_excess, summarize
from finalitybench.tasks import build_corpus
from finalitybench.world import EVAL_SEEDS

REPLICATES = 4000


def main() -> None:
    banner("E1 planner versus the baselines")
    corpus = build_corpus(n_tasks=320)
    prior = FinalityPrior.fit(corpus)
    policies = baseline_policies() + [FinalityAwarePlanner(prior)]
    grades = evaluate(policies, corpus, profile=FaultProfile(), seeds=EVAL_SEEDS)

    by: dict[str, list] = {}
    for g in grades:
        by.setdefault(g.policy, []).append(g)
    pairs = pair_map(corpus)

    rows = []
    for policy in policies:
        s = summarize(grades, policy.name)
        mine = by[policy.name]
        rows.append({
            **s.as_dict(),
            "paired": paired_excess(grades, corpus, policy.name),
            "by_archetype": by_archetype(grades, policy.name),
            "ci": {
                "exact_rate": bootstrap(mine, exact_rate, pair_of=pairs,
                                        replicates=REPLICATES).as_dict(),
                "mean_excess": bootstrap(mine, mean_gap, pair_of=pairs,
                                         replicates=REPLICATES).as_dict(),
                "pass_all": bootstrap(mine, pass_all_seeds, pair_of=pairs,
                                      replicates=REPLICATES).as_dict(),
                "premature": bootstrap(mine, premature_rate, pair_of=pairs,
                                       replicates=REPLICATES).as_dict(),
            },
        })

    # Every baseline against the planner, on a shared resample.
    comparisons = {}
    for policy in policies:
        if policy.name == "planner":
            continue
        comparisons[policy.name] = {
            "mean_gap": paired_difference(by["planner"], by[policy.name], mean_gap,
                                          pair_of=pairs, replicates=REPLICATES).as_dict(),
            "exact_rate": paired_difference(by["planner"], by[policy.name], exact_rate,
                                            pair_of=pairs, replicates=REPLICATES).as_dict(),
        }

    save("e1_main", {
        "provenance": provenance(experiment="e1_main"),
        "corpus": corpus.stats(), "prior": prior.as_dict(),
        "seeds": list(EVAL_SEEDS), "n_grades": len(grades),
        "bootstrap": {"replicates": REPLICATES, "units": "task, pairs collapsed"},
        "policies": rows, "planner_vs": comparisons,
    })

    hdr = (f"  {'policy':16s}{'exact rate (95% CI)':>26s}"
           f"{'mean gap $ (95% CI)':>28s}")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for r in rows:
        e = r["ci"]["exact_rate"]
        m = r["ci"]["mean_excess"]
        exact = f"{e['point']:.3f} [{e['low']:.3f}, {e['high']:.3f}]"
        gap = f"{m['point']/100:.2f} [{m['low']/100:.2f}, {m['high']/100:.2f}]"
        print(f"  {r['policy']:16s}{exact:>26s}{gap:>28s}")

    print("\n  planner minus baseline, shared task resample:")
    for name, d in comparisons.items():
        g = d["mean_gap"]
        spans = (g["low"] < 0) != (g["high"] < 0)
        note = "  spans zero" if spans else ""
        print(f"    vs {name:16s} ${g['point']/100:+7.2f} "
              f"[{g['low']/100:+7.2f}, {g['high']/100:+7.2f}]{note}")


if __name__ == "__main__":
    main()
