"""E6 -- the worked example, computed rather than asserted.

The paper walks two cases at one instant: a large order the planner closes and
a small one it ships, with the four action values written out and the gate
escalating in both. Those numbers are arithmetic over the planner's own
constants -- the dispute cost, the escalation fee, the cost-of-goods rate --
and every one of them was typed into the paragraph by hand. Change a constant
and the paper keeps the old arithmetic, which is worse than having no example,
because the example is where a reader checks their understanding.

So compute them, from the same function the planner calls. The prose keeps its
story; the figures come from ``value_terminal_actions``.

The instant is the one the paragraph describes: past the ship-by deadline for
the large order, with the capture unresolved and the belief at even odds. Even
odds is the interesting case rather than a convenient one -- it is where
shipping and closing are closest and the decision actually turns on the order
value, which is the point the paragraph makes.
"""

from __future__ import annotations

from _common import provenance, save

from fap.planner import value_terminal_actions
from finalitybench import config

#: The two orders the paragraph contrasts, in cents.
LARGE = 29900
SMALL = 2499
#: The belief at the deciding instant: the capture is a coin flip.
P_SETTLE = 0.5
#: Whether the money lands after the analyst has looked. The paragraph's
#: analyst picks the case up after the deadline and finds it already there.
P_SETTLES_LATE = 0.0


def value(amount: int, *, can_ship: bool) -> dict:
    v = value_terminal_actions(amount, config.cogs_of(amount), P_SETTLE,
                               can_ship=can_ship, p_settles_late=P_SETTLES_LATE)
    return {k: (None if x is None else round(x / 100, 2))
            for k, x in v.as_dict().items()}


def main() -> None:
    large = value(LARGE, can_ship=True)
    small = value(SMALL, can_ship=True)

    def best(v: dict) -> str:
        return max((k for k, x in v.items() if x is not None),
                   key=lambda k: v[k])

    large_best, small_best = best(large), best(small)
    save("e6_worked_example", {
        "provenance": provenance(),
        "config": {"large_cents": LARGE, "small_cents": SMALL,
                   "p_settle": P_SETTLE, "p_settles_late": P_SETTLES_LATE,
                   "dispute_cost_cents": config.DISPUTE_COST,
                   "escalation_cost_cents": config.ESCALATION_COST,
                   "cogs_rate": config.COGS_RATE},
        "large": {"amount": round(LARGE / 100, 2), "values": large,
                  "chooses": large_best,
                  "cogs": round(config.cogs_of(LARGE) / 100, 2),
                  "saved_over_escalating": round(
                      large[large_best] - large["escalate"], 2)},
        "small": {"amount": round(SMALL / 100, 2), "values": small,
                  "chooses": small_best,
                  "cogs": round(config.cogs_of(SMALL) / 100, 2),
                  "saved_over_escalating": round(
                      small[small_best] - small["escalate"], 2)},
        "headline": {
            "the_large_order_is_closed": large_best == "close",
            "the_small_order_is_shipped": small_best == "ship",
            "the_gate_escalates_either_way_for": round(
                config.ESCALATION_COST / 100, 2),
            "note": ("the two orders differ only in value, and the planner's "
                     "choice flips while the gate's does not -- which is the "
                     "paragraph's point"),
        },
    })


if __name__ == "__main__":
    main()
