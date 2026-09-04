"""E5 -- what a shield is worth, and to whom.

The ablation in E2 finds the shield worth nothing inside the planner. That is
not a defect and it has a cause: the planner already picks the highest expected
value, so a rule that blocks anything below the best reversible alternative can
never fire.

A shield should therefore be tested where it might matter, around policies that
do not maximise expected value. Two criteria are compared. The expected-value
shield turns out to block almost nothing, because at the settle rate this corpus
exhibits, shipping without checking is a bet that pays: goods cost sixty per
cent of the order and roughly seventy per cent of captures settle. The
downside shield objects to the same action on the grounds that the branch it
cannot rule out is ruinous.

When it objects, the shield asks the agent to look rather than forbidding it to
act. Vetoing turns a policy that gambles into one that never moves, which is
not an improvement.
"""

from __future__ import annotations

from _common import banner, pair_map, provenance, save

from fap.belief import FinalityPrior
from fap.planner import Shielded
from finalitybench.faults import FaultProfile
from finalitybench.policies import (
    EagerPolicy,
    MajorityVotePolicy,
    OptimisticPolicy,
    ReActPolicy,
)
from finalitybench.runner import evaluate, paired_excess, summarize
from finalitybench.tasks import build_corpus
from finalitybench.world import EVAL_SEEDS

SUBJECTS = (("optimistic", OptimisticPolicy), ("eager", EagerPolicy),
            ("majority", MajorityVotePolicy), ("react", ReActPolicy))


def main() -> None:
    banner("E5 the shield as a wrapper")
    corpus = build_corpus(n_tasks=320)
    prior = FinalityPrior.fit(corpus)

    policies, meta = [], {}
    for name, factory in SUBJECTS:
        policies.append(factory())
        for criterion in ("expected", "downside"):
            w = Shielded(factory(), prior)
            w._shield.criterion = criterion
            w.name = f"{name}+{criterion}"
            policies.append(w)
            meta[w.name] = w

    grades = evaluate(policies, corpus, profile=FaultProfile(), seeds=EVAL_SEEDS)
    rows = []
    for p in policies:
        s = summarize(grades, p.name)
        pe = paired_excess(grades, corpus, p.name)
        rows.append({
            "policy": p.name, "exact_rate": s.exact_rate,
            "mean_excess": s.mean_excess, "paired": pe["mean_pair_excess"],
            "premature_rate": s.premature_rate,
            "blocks": getattr(meta.get(p.name), "blocks", 0),
            "redirects": getattr(meta.get(p.name), "redirects", 0),
        })

    save("e5_shield", {
        "provenance": provenance(experiment="e5_shield"),
        "corpus": corpus.stats(), "rows": rows,
    })

    print(f"  {'policy':22s}{'exact':>9s}{'mean $':>10s}{'paired $':>11s}{'prem':>7s}{'blocks':>8s}")
    for r in rows:
        print(f"  {r['policy']:22s}{r['exact_rate']:9.1%}{r['mean_excess']/100:10.2f}"
              f"{r['paired']/100:11.2f}{r['premature_rate']:7.1%}{r['blocks']:8d}")


if __name__ == "__main__":
    main()
