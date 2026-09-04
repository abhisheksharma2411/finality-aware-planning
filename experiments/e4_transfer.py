"""E4 -- does the fitted belief transfer to a corpus it was not fitted on?

The planner's prior is estimated from the public split. If its advantage came
from having memorised that particular draw, it would shrink on the regenerated
split, which the benchmark provides for exactly this purpose.

Three conditions. The prior fitted on the split being evaluated is an upper
bound the planner is not entitled to; the prior fitted on the public split is
what an honest deployment looks like; a deliberately wrong prior shows how much
the fit is worth at all.
"""

from __future__ import annotations

from _common import banner, pair_map, provenance, save

from fap.belief import FinalityPrior
from fap.planner import FinalityAwarePlanner
from finalitybench.bootstrap import mean_gap, paired_difference
from finalitybench.faults import FaultProfile
from finalitybench.policies import TransactionalRuntimePolicy
from finalitybench.runner import evaluate, summarize
from finalitybench.tasks import build_splits
from finalitybench.world import EVAL_SEEDS


def main() -> None:
    banner("E4 does the fitted prior transfer?")
    splits = build_splits(n_tasks=320)
    public, hidden = splits["public"], splits["hidden"]
    fitted_public = FinalityPrior.fit(public)
    fitted_hidden = FinalityPrior.fit(hidden)
    # A prior that says captures resolve early and nearly always settle, which
    # is what an optimistic guess would look like.
    wrong = FinalityPrior([100] * 200 + [200] * 121, 0.95, "deliberately wrong",
                          [(100, True)] * 200 + [(200, True)] * 121)

    rows = []
    for split_name, corpus in (("public", public), ("hidden", hidden)):
        for label, prior in (("fitted on public", fitted_public),
                             ("fitted on this split", fitted_hidden if
                              split_name == "hidden" else fitted_public),
                             ("deliberately wrong", wrong)):
            policies = [TransactionalRuntimePolicy(), FinalityAwarePlanner(prior)]
            grades = evaluate(policies, corpus, profile=FaultProfile(), seeds=EVAL_SEEDS)
            by: dict[str, list] = {}
            for g in grades:
                by.setdefault(g.policy, []).append(g)
            d = paired_difference(by["planner"], by["transactional"], mean_gap,
                                  pair_of=pair_map(corpus), replicates=1500)
            rows.append({
                "split": split_name, "prior": label,
                "prior_source": prior.source,
                "gate": summarize(grades, "transactional").mean_excess,
                "planner": summarize(grades, "planner").mean_excess,
                "planner_exact": summarize(grades, "planner").exact_rate,
                "difference": d.as_dict(),
                "planner_better": d.high < 0,
            })

    save("e4_transfer", {
        "provenance": provenance(experiment="e4_transfer"),
        "public": public.stats(), "hidden": hidden.stats(),
        "priors": {"public": fitted_public.as_dict(), "hidden": fitted_hidden.as_dict()},
        "rows": rows,
    })

    print(f"  {'split':8s}{'prior':24s}{'gate $':>9s}{'planner $':>11s}{'difference':>26s}")
    for r in rows:
        d = r["difference"]
        mark = "  better" if r["planner_better"] else "  ns"
        print(f"  {r['split']:8s}{r['prior']:24s}{r['gate']/100:9.2f}{r['planner']/100:11.2f}"
              f"{d['point']/100:+8.2f} [{d['low']/100:+6.2f},{d['high']/100:+6.2f}]{mark}")


if __name__ == "__main__":
    main()
