"""Escalation as a capability, not a constant.

Section~\\ref{sec:results} reports that most of the margin over the finality
gate comes from cases the benchmark calls unresolvable, where the gate escalates
and this rule does not. That number is a statement about what an escalated case
is worth, and FinalityBench fixes that by modelling the analyst as someone who
completes the disposition of money already held and starts no new money
movement. It is a deliberate and defensible choice, and it is one choice.

Under it, escalation cannot rescue a case whose capture never settles, so
declining to escalate is nearly free. An analyst who may re-attempt a failed
capture changes that: on a case where a retry would have succeeded, escalating
recovers the order and the decision rule's refusal to escalate becomes a
mistake. The question is not whether the rule beats one analyst but at what
analyst capability it stops beating them.

This module re-scores an episode under an analyst of a stated capability,
without modifying the benchmark. Grading happens after the episode has run, so
the recovery an analyst would have achieved can be computed from the log and
the case's own ``retry_succeeds`` flag, and the position adjusted. Nothing in
the environment is patched and no benchmark result changes.
"""

from __future__ import annotations

from dataclasses import dataclass

from finalitybench import config


@dataclass(frozen=True)
class Analyst:
    """What a human on the exception queue is able to do.

    ``retry_success`` is the probability that a re-attempted capture settles on
    a case where the benchmark says a retry would have worked. Zero is
    FinalityBench's own analyst, who never re-attempts. One is an analyst who
    always does and always succeeds when the case permits it.
    """

    retry_success: float = 0.0
    label: str = "benchmark"

    def recovers(self, case) -> bool:
        """Would this analyst recover an otherwise-unrecoverable case?"""
        return self.retry_success > 0.0 and bool(case.retry_succeeds)


def adjusted_excess(grade, case, analyst: Analyst) -> float:
    """Excess loss for one graded episode under a more capable analyst.

    Only escalated episodes can differ, and only on cases where a retry would
    have settled. The recovery is worth the order's margin: the analyst
    collects the amount and gives up the cost of goods, which is what shipping
    would have achieved had the capture resolved in time.

    The expectation is taken over ``retry_success`` rather than sampled, so the
    sweep is smooth and two capabilities differing slightly do not differ by
    sampling noise.
    """
    base = float(grade.excess_loss)
    if not grade.escalated or not analyst.recovers(case):
        return base
    margin = case.amount - config.cogs_of(case.amount)
    recovered = analyst.retry_success * min(base, float(margin))
    return base - recovered


def sweep(grades, cases: dict, capabilities) -> list[dict]:
    """Mean excess for each policy at each analyst capability."""
    by_id = cases
    out = []
    for cap in capabilities:
        analyst = Analyst(retry_success=cap, label=f"retry={cap:.2f}")
        totals: dict[str, list[float]] = {}
        for g in grades:
            case = by_id[g.task_id]
            totals.setdefault(g.policy, []).append(
                adjusted_excess(g, case, analyst))
        out.append({
            "retry_success": cap,
            "mean_excess": {p: sum(v) / len(v) for p, v in sorted(totals.items())},
        })
    return out
