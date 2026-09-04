"""E2 -- which part of the planner does the work?

Four variants against the full planner. Each removes one component and keeps
everything else, so the difference is attributable.

``no shield``     the expected-value comparison still runs, but nothing refuses
                  an irreversible action the belief does not support.
``no VoI``        probe on a fixed schedule rather than only when the answer
                  could have changed.
``marginal prior`` use the overall settle rate instead of the rate conditional
                  on the capture still being unresolved. This is the tempting
                  shortcut and it is wrong: captures that resolve late are not a
                  random sample of captures.
``fixed escalate`` keep the belief and the probing, but always escalate at the
                  deadline. This is the finality gate wearing the planner's
                  machinery, and it isolates the decision rule itself.
"""

from __future__ import annotations

from _common import banner, pair_map, provenance, save

from fap.belief import FinalityPrior
from fap.planner import FinalityAwarePlanner
from finalitybench.bootstrap import exact_rate, mean_gap, paired_difference
from finalitybench.env import Action
from finalitybench.faults import FaultProfile
from finalitybench.runner import evaluate, summarize
from finalitybench.tasks import build_corpus
from finalitybench.world import EVAL_SEEDS


class MarginalPriorPlanner(FinalityAwarePlanner):
    """The planner, told to use the unconditional settle rate."""

    name = "no-conditional-prior"

    def reset(self, case=None):
        super().reset(case)
        flat = self._prior.settle_rate
        self._belief.prior = _Flat(self._prior, flat)


class _Flat:
    """A prior whose settle rate ignores what has already been ruled out."""

    def __init__(self, inner, rate):
        self._inner, self._rate = inner, rate

    def __getattr__(self, item):
        return getattr(self._inner, item)

    def settle_rate_after(self, t):
        return self._rate


class AlwaysEscalatePlanner(FinalityAwarePlanner):
    """The planner's machinery with the gate's decision rule."""

    name = "fixed-escalate"

    def act(self, obs):
        action = super().act(obs)
        if action.tool in ("ship", "close", "refund") and self.decisions:
            if self.decisions[-1]["now"] == obs["now"]:
                return Action("escalate", {"reason": "fixed rule"})
        return action


def main() -> None:
    banner("E2 ablations")
    corpus = build_corpus(n_tasks=320)
    prior = FinalityPrior.fit(corpus)
    variants = [
        FinalityAwarePlanner(prior),
        FinalityAwarePlanner(prior, shield=False),
        FinalityAwarePlanner(prior, use_voi=False),
        MarginalPriorPlanner(prior),
        AlwaysEscalatePlanner(prior),
    ]
    variants[1].name = "no-shield"
    variants[2].name = "no-voi"

    grades = evaluate(variants, corpus, profile=FaultProfile(), seeds=EVAL_SEEDS)
    by: dict[str, list] = {}
    for g in grades:
        by.setdefault(g.policy, []).append(g)
    pairs = pair_map(corpus)

    rows = []
    for v in variants:
        s = summarize(grades, v.name)
        entry = {"variant": v.name, **s.as_dict()}
        if v.name != "planner":
            d = paired_difference(by[v.name], by["planner"], mean_gap,
                                  pair_of=pairs, replicates=2000)
            e = paired_difference(by[v.name], by["planner"], exact_rate,
                                  pair_of=pairs, replicates=2000)
            entry["vs_planner_mean_gap"] = d.as_dict()
            entry["vs_planner_exact"] = e.as_dict()
        rows.append(entry)

    save("e2_ablation", {
        "provenance": provenance(experiment="e2_ablation"),
        "corpus": corpus.stats(), "seeds": list(EVAL_SEEDS), "rows": rows,
    })

    print(f"  {'variant':22s}{'exact':>9s}{'mean gap $':>13s}{'cost of removing it':>26s}")
    for r in rows:
        delta = ""
        if "vs_planner_mean_gap" in r:
            d = r["vs_planner_mean_gap"]
            spans = (d["low"] < 0) != (d["high"] < 0)
            delta = (f"{d['point']/100:+7.2f} [{d['low']/100:+6.2f},{d['high']/100:+6.2f}]"
                     + ("  ns" if spans else ""))
        print(f"  {r['variant']:22s}{r['exact_rate']:9.1%}"
              f"{r['mean_excess']/100:13.2f}{delta:>26s}")


if __name__ == "__main__":
    main()
