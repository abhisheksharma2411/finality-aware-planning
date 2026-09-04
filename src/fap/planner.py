"""A finality-aware planner, and the shield that keeps it honest.

The benchmark's strongest shipped policy gates irreversible actions on an
authoritative probe and escalates to a human when the probe still says
``unknown`` at the deadline. That is safe, and on this corpus it is never the
best available action: escalation costs a flat fee on every case, while the
alternatives cost something that depends on the order.

The planner replaces the fixed escalate rule with an expected-value comparison
under a belief fitted from the public split. Everything else it does -- probe,
wait, retry under the original key -- matches the gate, so the difference
between them isolates the one decision this paper is about.

The shield is separate from the planner on purpose. The planner proposes; the
shield refuses irreversible actions whose expected value is worse than the best
reversible alternative. Keeping them apart means the shield can be ablated, and
Section on ablations reports what happens when it is.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._p1 import ensure_p1
from .belief import Belief, FinalityPrior

ensure_p1()

from finalitybench import config  # noqa: E402
from finalitybench.env import Action, RETRY_LATENCY  # noqa: E402
from finalitybench.policies import Policy  # noqa: E402
from finalitybench.world import Case  # noqa: E402

#: When the analyst picks up an escalated case, in ticks after the ship-by date.
ANALYST_DELAY = 200


@dataclass(frozen=True)
class Valuation:
    """Expected terminal position of each available disposition, in cents."""

    ship: float | None
    close: float
    escalate: float
    refund: float

    def best(self) -> tuple[str, float]:
        options = [("close", self.close), ("escalate", self.escalate),
                   ("refund", self.refund)]
        if self.ship is not None:
            options.append(("ship", self.ship))
        return max(options, key=lambda kv: kv[1])

    def as_dict(self) -> dict[str, float]:
        return {"ship": self.ship, "close": self.close,
                "escalate": self.escalate, "refund": self.refund}


def value_terminal_actions(amount: int, cogs: int, p_settle: float,
                           can_ship: bool, p_settles_late: float) -> Valuation:
    """Expected position of each disposition under the current belief.

    ``ship``      collect the order if the capture settles, lose the goods if
                  it does not. Unavailable past the ship-by date.
    ``close``     do nothing. Costs a dispute whenever money arrives for an
                  order that was never fulfilled.
    ``escalate``  hand to an analyst, who returns the money if it has arrived by
                  the time they look. Costs a flat fee always, and still incurs
                  the dispute when the money lands after they have looked.
    ``refund``    return money that may never have arrived, which is why it is
                  almost always the worst option and is included to show that.
    """
    dispute = config.DISPUTE_COST
    escalation = config.ESCALATION_COST
    return Valuation(
        ship=(p_settle * amount - cogs) if can_ship else None,
        close=-p_settle * dispute,
        escalate=-escalation - dispute * p_settles_late,
        refund=-(1.0 - p_settle) * amount,
    )


class Shield:
    """Refuses an irreversible action the belief does not support.

    Two criteria, and the difference between them is the point.

    ``expected`` allows an irreversible action whose expected value is at least
    that of the best reversible alternative. It has no free parameter and it
    turns out to block almost nothing, because at the settle rate this corpus
    actually exhibits, shipping blind is expected-value positive: the goods cost
    sixty per cent of the order and the capture settles seventy-two per cent of
    the time. An expected-value shield cannot object to a bet that pays.

    ``downside`` allows it only when the outcome the agent cannot rule out is
    survivable: the loss in the bad branch must not exceed the best reversible
    alternative by more than ``tolerance``. This is a risk criterion rather than
    a mean one, and it is what refuses a bet that is profitable on average and
    ruinous on the case in front of you.

    Which is correct depends on what the operator is optimising, and this
    package does not claim one is right. It reports what each does.
    """

    name = "shield"

    def __init__(self, enabled: bool = True, criterion: str = "downside",
                 tolerance: int = 0) -> None:
        self.enabled = enabled
        self.criterion = criterion
        self.tolerance = tolerance
        self.blocks = 0

    def allows(self, action: str, valuation: Valuation,
               worst_case: float | None = None) -> bool:
        if not self.enabled or action not in ("ship", "refund"):
            return True
        proposed = valuation.ship if action == "ship" else valuation.refund
        if proposed is None:
            self.blocks += 1
            return False
        reversible = max(valuation.close, valuation.escalate)
        if self.criterion == "expected":
            ok = proposed >= reversible
        else:
            ok = worst_case is None or worst_case >= reversible - self.tolerance
        if not ok:
            self.blocks += 1
        return ok


class FinalityAwarePlanner(Policy):
    """Probe, wait while the information is worth acquiring, then value the
    remaining options and take the best one."""

    name = "planner"

    def __init__(self, prior: FinalityPrior | None = None, *,
                 shield: bool = True, use_voi: bool = True,
                 probe_interval: int = 60) -> None:
        self._prior = prior or FinalityPrior.fit()
        self._shield = Shield(shield, criterion="expected")
        self.use_voi = use_voi
        self.probe_interval = probe_interval
        self.decisions: list[dict[str, Any]] = []

    def reset(self, case: Case | None = None) -> None:
        super().reset(case)
        self._belief = Belief(self._prior)
        self._retried = False
        self._probe_count = 0
        self._waited_since_probe = False

    # -- helpers -----------------------------------------------------------

    def _worth_probing(self, obs: dict[str, Any]) -> bool:
        """Value of information: probe only if the answer could have changed.

        A probe costs five ticks against a read's one, and its only use is to
        detect a resolution that has happened since the last one. When the
        belief says almost no probability mass has accrued in that window, the
        call buys nothing and the deadline is better spent waiting.
        """
        if not self.use_voi:
            return True
        since = self._belief.last_unknown_at
        if since < 0:
            return True          # nothing observed yet, so the first probe always pays
        gained = self._prior.resolves_within(since, obs["now"])
        return gained > 0.02

    # -- the policy --------------------------------------------------------

    def act(self, obs: dict[str, Any]) -> Action:
        case: Case = self._case
        now = obs["now"]
        ref = obs["case"]["capture_ref"]
        amount = obs["case"]["order_amount"]
        deadline = obs["sla_deadline"]

        probe = self._fresh(obs, "probe_processor")
        if probe is not None and probe.get("ref") == ref:
            self._belief.observe_probe(probe.get("status", "unknown"), now)

        # A resolved capture needs no planning.
        if self._belief.known == "settled":
            return Action("ship")
        if self._belief.known == "failed":
            retried = self._last(obs, "retry_capture")
            if retried is None:
                if deadline - now < RETRY_LATENCY:
                    return Action("close")     # no time for a replacement to land
                return Action("retry_capture", {"idem_key": ref})
            if not retried.get("accepted"):
                return Action("close")
            # The replacement is a new capture with its own outcome, and it is
            # no more knowable in advance than the original was. Shipping on the
            # strength of having submitted it is exactly the premature action
            # this benchmark exists to catch; an earlier version of this planner
            # did it and gave away the cost of goods on every unrecoverable
            # failure.
            new_ref = retried.get("ref")
            follow = self._fresh(obs, "probe_processor")
            if follow is not None and follow.get("ref") == new_ref:
                if follow.get("status") == "settled":
                    return Action("ship") if now <= deadline else Action("close")
                if follow.get("status") == "failed":
                    return Action("close")
            if deadline - now > config.PROBE_COST:
                return Action("probe_processor", {"ref": new_ref})
            return Action("close")

        # Still unknown. Is another observation worth its cost?
        time_left = deadline - now
        if probe is None and self._worth_probing(obs) and time_left > config.PROBE_COST:
            self._probe_count += 1
            return Action("probe_processor", {"ref": ref})

        if time_left > self.probe_interval + config.PROBE_COST:
            return Action("wait", {"ticks": self.probe_interval})

        # The deadline is here and the outcome is not known. Value the options.
        cogs = config.cogs_of(amount)
        p_settle = self._belief.settle_probability()
        p_late = self._prior.resolves_within(
            max(now, self._belief.last_unknown_at), deadline + ANALYST_DELAY)
        valuation = value_terminal_actions(
            amount, cogs, p_settle, can_ship=now <= deadline,
            p_settles_late=p_settle * (1.0 - p_late))

        choice, value = valuation.best()
        if not self._shield.allows(choice, valuation):
            choice = "close" if valuation.close >= valuation.escalate else "escalate"

        self.decisions.append({
            "task": case.task_id, "now": now, "amount": amount,
            "p_settle": round(p_settle, 3), "choice": choice,
            "values": valuation.as_dict(),
        })
        if choice == "ship":
            return Action("ship")
        if choice == "refund":
            return Action("refund", {"amount": amount})
        if choice == "escalate":
            return Action("escalate", {"reason": "finality not established"})
        return Action("close")


class Shielded(Policy):
    """Wrap any policy so the shield vets its irreversible actions.

    The ablation in E2 shows the shield is worth nothing inside the planner,
    which is not a defect: the planner already chooses the highest expected
    value, so a rule that blocks actions below the best reversible alternative
    can never fire. A shield earns its place around a policy that does *not*
    maximise expected value, and that is what this wrapper tests.

    The wrapped policy proposes. The shield substitutes the best reversible
    action when the proposal is irreversible and the belief does not support it.
    """

    def __init__(self, inner: Policy, prior: FinalityPrior | None = None) -> None:
        self._inner = inner
        self._prior = prior or FinalityPrior.fit()
        self._shield = Shield(True)
        self.name = f"shielded-{inner.name}"

    @property
    def blocks(self) -> int:
        return self._shield.blocks

    @property
    def redirects(self) -> int:
        return getattr(self, "_redirects", 0)

    def reset(self, case: Case | None = None) -> None:
        self._inner.reset(case)
        self._case = case
        self._belief = Belief(self._prior)
        self._redirects = 0

    def act(self, obs: dict[str, Any]) -> Action:
        proposed = self._inner.act(obs)
        if proposed.tool not in ("ship", "refund"):
            return proposed

        ref = obs["case"]["capture_ref"]
        probe = self._fresh(obs, "probe_processor")
        if probe is not None and probe.get("ref") == ref:
            self._belief.observe_probe(probe.get("status", "unknown"), obs["now"])
        # A settled capture makes shipping safe and needs no shield.
        if self._belief.known == "settled":
            return proposed

        amount = obs["case"]["order_amount"]
        valuation = value_terminal_actions(
            amount, config.cogs_of(amount), self._belief.settle_probability(),
            can_ship=obs["now"] <= obs["sla_deadline"],
            p_settles_late=0.0,
        )
        # The branch the agent cannot rule out: the capture fails and the goods
        # are gone, or a refund is paid on money that never arrived.
        worst = -config.cogs_of(amount) if proposed.tool == "ship" else -float(amount)
        if self._shield.allows(proposed.tool, valuation, worst_case=worst):
            return proposed

        # A veto turns a policy that gambles into one that never acts, which is
        # not an improvement. Where the objection is that the agent does not
        # know enough, the useful substitution is to find out: the authoritative
        # probe costs five ticks and resolves the question the shield is
        # objecting to. Only when there is no deadline left for that does the
        # shield fall back to the best reversible action.
        if probe is None and obs["sla_deadline"] - obs["now"] > config.PROBE_COST:
            self._redirects += 1
            return Action("probe_processor", {"ref": ref})
        if valuation.close >= valuation.escalate:
            return Action("close")
        return Action("escalate", {"reason": "shield: belief does not support the action"})
