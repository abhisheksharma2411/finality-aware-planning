"""E7 -- the break-even point of a more capable analyst.

The margin over the finality gate is concentrated on cases the benchmark calls
unresolvable, where the gate escalates and the decision rule does not. Whether
that margin is real therefore depends on what an escalated case is worth, and
FinalityBench fixes that with an analyst who completes the disposition of money
already held and starts none. Under that model escalation cannot rescue a case
whose capture never settles, so declining to escalate costs almost nothing.

That is one model of a human, and the paper should not rest on it silently. So
sweep the analyst's capability: at each level, re-score every graded episode as
if an escalated case had that probability of being rescued by a re-attempted
capture, and find where the gate catches up.

The re-scoring is done after the fact, from the log and the case's own
``retry_succeeds`` flag. Nothing in the benchmark is patched, and its published
numbers are the ``retry\\_success = 0`` row of the sweep.
"""

from __future__ import annotations

from _common import banner, provenance, save

from fap.belief import FinalityPrior
from fap.escalation import sweep
from fap.planner import FinalityAwarePlanner
from finalitybench.faults import FaultProfile
from finalitybench.policies import TransactionalRuntimePolicy
from finalitybench.runner import evaluate
from finalitybench.tasks import build_corpus
from finalitybench.world import EVAL_SEEDS

N_TASKS = 320
CAPABILITIES = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)


def main() -> None:
    banner("E7 escalation capability")
    corpus = build_corpus(n_tasks=N_TASKS)
    prior = FinalityPrior.fit(corpus)

    planner = FinalityAwarePlanner(prior)
    gate = TransactionalRuntimePolicy()
    grades = evaluate([planner, gate], corpus, profile=FaultProfile(),
                      seeds=EVAL_SEEDS)
    cases = {c.task_id: c for c in corpus.cases}

    rows = sweep(grades, cases, CAPABILITIES)
    planner_name, gate_name = planner.name, gate.name

    for r in rows:
        r["gap"] = r["mean_excess"][gate_name] - r["mean_excess"][planner_name]
        r["planner_ahead"] = r["gap"] > 0

    ahead = [r["retry_success"] for r in rows if r["planner_ahead"]]
    behind = [r["retry_success"] for r in rows if not r["planner_ahead"]]
    baseline = next(r for r in rows if r["retry_success"] == 0.0)

    # Cases where a more capable analyst could have made a difference at all.
    escalated = {g.task_id for g in grades
                 if g.policy == gate_name and g.escalated}
    rescuable = sum(1 for t in escalated if cases[t].retry_succeeds)

    save("e7_escalation", {
        "provenance": provenance(),
        "config": {"n_tasks": N_TASKS, "seeds": list(EVAL_SEEDS),
                   "capabilities": list(CAPABILITIES),
                   "policies": [planner_name, gate_name]},
        "rows": rows,
        "headline": {
            "baseline_gap_cents": baseline["gap"],
            "gap_at_full_capability_cents": rows[-1]["gap"],
            "planner_ahead_at": ahead,
            "planner_behind_at": behind,
            "break_even_retry_success": (min(behind) if behind else None),
            "gate_escalations": len(escalated),
            "escalations_a_retry_could_rescue": rescuable,
            "share_rescuable": rescuable / max(1, len(escalated)),
            "note": ("retry_success = 0 is FinalityBench's own analyst and "
                     "reproduces the published gap; the sweep asks how capable "
                     "a human has to be before escalating unconditionally wins"),
        },
    })


if __name__ == "__main__":
    main()
