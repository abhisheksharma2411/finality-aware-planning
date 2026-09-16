"""E6 -- what shipping on submission costs, measured instead of remembered.

The planner verifies a replacement capture before shipping against it. That
line was added after an earlier version shipped as soon as the retry was
accepted, and the paper quoted a cost per unrecoverable case that came from
the session where it was fixed rather than from any results file. So it is
neither reproducible nor, as it turns out, checkable.

This reconstructs the earlier version -- identical except that an accepted
retry is enough to ship -- and runs both over the corpus. The comparison that
matters is on the archetypes where the replacement never settles, because that
is where the two differ: everywhere else the verification confirms what
shipping would have assumed.

Submitting a replacement says nothing about whether it will settle. Shipping on
that basis is the premature action the benchmark exists to detect, and the point
of measuring it is that the policy committing it was written to avoid it.
"""

from __future__ import annotations

from _common import banner, provenance, save

from fap.belief import FinalityPrior
from fap.planner import FinalityAwarePlanner
from finalitybench.faults import FaultProfile
from finalitybench.policies import Action
from finalitybench.runner import evaluate, summarize
from finalitybench.tasks import build_corpus
from finalitybench.world import EVAL_SEEDS


class ShipsOnSubmission(FinalityAwarePlanner):
    """The planner as it was before the verification step.

    Only the accepted-retry branch differs: where the current planner probes
    the replacement and ships only on a settled status, this one ships on the
    acceptance itself.
    """

    name = "planner_ships_on_submission"

    def act(self, obs):
        action = super().act(obs)
        retried = self._last(obs, "retry_capture")
        if (retried is not None and retried.get("accepted")
                and action.tool in ("probe_processor", "close")
                and obs["now"] <= obs["sla_deadline"]):
            return Action("ship")
        return action


def main() -> None:
    banner("E6 shipping on submission")
    corpus = build_corpus(n_tasks=320)
    prior = FinalityPrior.fit(corpus)

    current = FinalityAwarePlanner(prior)
    earlier = ShipsOnSubmission(prior)
    earlier.name = ShipsOnSubmission.name

    grades = evaluate([current, earlier], corpus,
                      profile=FaultProfile(), seeds=EVAL_SEEDS)

    def rows_for(name: str) -> dict:
        s = summarize(grades, name)
        return {"exact_rate": s.exact_rate, "mean_excess": s.mean_excess,
                "premature_rate": s.premature_rate}

    # Grade carries a task id, not an archetype; the corpus has the mapping.
    archetype_of = {c.task_id: c.archetype for c in corpus.cases}
    by_archetype: dict[str, dict] = {}
    for g in grades:
        slot = by_archetype.setdefault(archetype_of[g.task_id], {})
        arm = slot.setdefault(g.policy, {"n": 0, "excess": 0})
        arm["n"] += 1
        arm["excess"] += g.excess_loss

    per_archetype = []
    for archetype, arms in sorted(by_archetype.items()):
        if len(arms) != 2:
            continue
        cur = arms[current.name]
        old = arms[earlier.name]
        per_archetype.append({
            "archetype": archetype,
            "n": cur["n"],
            "current_mean_excess": cur["excess"] / cur["n"],
            "earlier_mean_excess": old["excess"] / old["n"],
            "cost_per_case": (old["excess"] - cur["excess"]) / cur["n"],
        })

    worst = max(per_archetype, key=lambda r: r["cost_per_case"])
    save("e6_premature", {
        "provenance": provenance(),
        "config": {"n_tasks": 320, "seeds": list(EVAL_SEEDS),
                   "arms": [current.name, earlier.name]},
        "per_archetype": per_archetype,
        "headline": {
            "current": rows_for(current.name),
            "earlier": rows_for(earlier.name),
            "worst_archetype": worst["archetype"],
            "cost_per_case_cents": worst["cost_per_case"],
            "cost_per_case_dollars": round(worst["cost_per_case"] / 100, 2),
            "premature_rate_increase": (rows_for(earlier.name)["premature_rate"]
                                        - rows_for(current.name)["premature_rate"]),
            "flagged_premature": (rows_for(earlier.name)["premature_rate"]
                                  > rows_for(current.name)["premature_rate"]),
            "note": (
                "the loss is real and the premature flag does not move. "
                "FinalityBench sets that flag when the agent ships while the "
                "*original* capture reference is undetermined, and on these "
                "archetypes the original has already failed by the time a "
                "replacement is submitted. Shipping against an unsettled "
                "replacement is the same mistake against a different "
                "reference, and the flag does not see it -- so the cost "
                "appears in excess loss alone. Recorded here because the "
                "paper previously described this as the premature action the "
                "benchmark detects, and the benchmark does not detect it."),
        },
    })


if __name__ == "__main__":
    main()
