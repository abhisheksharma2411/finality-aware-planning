"""What the agent can believe about finality, and how that belief updates.

The only latent fact that matters is when the pending capture resolves and
which way. An authoritative probe reveals it exactly when it has happened and
returns ``unknown`` otherwise, so a probe that comes back unknown at time ``t``
carries real information: it rules out every resolution time at or before
``t``. The belief is therefore the prior over resolution time, truncated by the
latest unknown probe.

The prior is fitted from the public split rather than assumed. That is the
split the benchmark publishes for exactly this purpose, and fitting on it and
reporting on the regenerated split is what makes the fit an honest one.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass, field
from typing import Sequence

from ._p1 import ensure_p1

ensure_p1()

from finalitybench.faults import FaultProfile  # noqa: E402
from finalitybench.tasks import Corpus, build_corpus  # noqa: E402


@dataclass
class FinalityPrior:
    """Empirical distribution of resolution time and outcome.

    Stored as a sorted list of observed resolution times plus the marginal rate
    at which captures settle. Both come from the public split; nothing here
    reads a case's hidden fields at decision time.
    """

    resolution_times: list[int] = field(default_factory=list)
    settle_rate: float = 0.5
    source: str = "unfitted"
    #: (resolution time, settled?) pairs, sorted by time. Needed because the
    #: marginal settle rate is the wrong number to plan with: captures that
    #: resolve late are not a random sample of captures. Using the marginal
    #: 0.72 here would tell the planner to ship every case it could not resolve,
    #: when the ones it cannot resolve are close to a coin flip.
    observations: list[tuple[int, bool]] = field(default_factory=list)

    @staticmethod
    def fit(corpus: Corpus | None = None) -> "FinalityPrior":
        corpus = corpus or build_corpus(n_tasks=320)
        obs = sorted((c.t_det, c.outcome == "settle") for c in corpus.cases)
        times = [t for t, _ in obs]
        settles = sum(1 for _, s in obs if s)
        return FinalityPrior(times, settles / max(1, len(obs)),
                             f"{corpus.split}:{corpus.fingerprint()}", obs)

    def settle_rate_after(self, t: int) -> float:
        """P(settles | resolution time > t).

        Conditional, not marginal. Captures still unresolved at the deadline
        are drawn from the tail, and the tail is not representative.
        """
        tail = [s for time, s in self.observations if time > t]
        if len(tail) < 8:
            return self.settle_rate
        return sum(1 for s in tail if s) / len(tail)

    def survival(self, t: int) -> float:
        """P(resolution has not happened by t)."""
        if not self.resolution_times:
            return 0.5
        idx = bisect.bisect_right(self.resolution_times, t)
        return 1.0 - idx / len(self.resolution_times)

    def resolves_within(self, now: int, horizon: int) -> float:
        """P(resolves in (now, horizon] | not resolved by now).

        The conditioning is the whole point: every probe that returns unknown
        moves ``now`` forward and shrinks the mass still available before the
        deadline.
        """
        remaining = self.survival(now)
        if remaining <= 1e-9:
            return 0.0
        later = self.survival(horizon)
        return max(0.0, (remaining - later) / remaining)

    def as_dict(self) -> dict:
        return {"n": len(self.resolution_times), "settle_rate": self.settle_rate,
                "source": self.source,
                "settle_rate_after": {t: round(self.settle_rate_after(t), 3)
                                      for t in (0, 300, 500, 600, 700)},
                "quantiles": {q: self._q(q) for q in (0.1, 0.25, 0.5, 0.75, 0.9)}}

    def _q(self, q: float) -> int:
        if not self.resolution_times:
            return 0
        i = min(len(self.resolution_times) - 1,
                int(q * (len(self.resolution_times) - 1)))
        return self.resolution_times[i]


@dataclass
class Belief:
    """The agent's state of knowledge during one episode."""

    prior: FinalityPrior
    last_unknown_at: int = -1
    known: str | None = None          # "settled" | "failed" once a probe says so
    probes: int = 0

    def observe_probe(self, status: str, at: int) -> None:
        self.probes += 1
        if status == "unknown":
            self.last_unknown_at = max(self.last_unknown_at, at)
        else:
            self.known = status

    @property
    def resolved(self) -> bool:
        return self.known is not None

    def resolves_before(self, deadline: int, now: int) -> float:
        """Probability the outcome becomes visible in time to act on it."""
        if self.resolved:
            return 1.0
        floor = max(now, self.last_unknown_at)
        return self.prior.resolves_within(floor, deadline)

    def settle_probability(self) -> float:
        if self.known == "settled":
            return 1.0
        if self.known == "failed":
            return 0.0
        return self.prior.settle_rate_after(self.last_unknown_at)
