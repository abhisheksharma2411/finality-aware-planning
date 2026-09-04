"""Tests for the properties the paper claims."""

from __future__ import annotations

import pytest

from fap.belief import Belief, FinalityPrior
from fap.planner import (
    FinalityAwarePlanner,
    Shield,
    Shielded,
    value_terminal_actions,
)
from finalitybench import config
from finalitybench.bootstrap import mean_gap, paired_difference
from finalitybench.env import Action
from finalitybench.faults import FaultProfile
from finalitybench.policies import OptimisticPolicy, TransactionalRuntimePolicy
from finalitybench.runner import evaluate, run_episode, summarize
from finalitybench.tasks import build_corpus
from finalitybench.world import EVAL_SEEDS


@pytest.fixture(scope="module")
def corpus():
    return build_corpus(n_tasks=320)


@pytest.fixture(scope="module")
def prior(corpus):
    return FinalityPrior.fit(corpus)


@pytest.fixture(scope="module")
def grades(corpus, prior):
    return evaluate([TransactionalRuntimePolicy(), FinalityAwarePlanner(prior)],
                    corpus, profile=FaultProfile(), seeds=EVAL_SEEDS)


# --- the belief ------------------------------------------------------------

def test_survival_is_monotone(prior):
    values = [prior.survival(t) for t in range(0, 1800, 60)]
    assert all(a >= b for a, b in zip(values, values[1:]))
    assert values[0] == pytest.approx(1.0, abs=0.02)


def test_unknown_probe_shrinks_the_available_mass(prior):
    belief = Belief(prior)
    early = belief.resolves_before(600, 120)
    belief.observe_probe("unknown", 500)
    late = belief.resolves_before(600, 500)
    assert late < early


def test_settle_rate_is_conditional_not_marginal(prior):
    """A capture still open at the deadline is not a typical capture.

    Planning with the marginal rate is the mistake this guards against; the
    ablation shows it costs real money.
    """
    assert prior.settle_rate > 0.65
    assert prior.settle_rate_after(600) < prior.settle_rate
    assert prior.settle_rate_after(600) == pytest.approx(0.5, abs=0.1)


# --- the valuation ---------------------------------------------------------

def test_escalation_is_never_the_best_option_at_default_costs():
    """The claim the planner's advantage rests on."""
    for amount in (2499, 29900, 349900):
        v = value_terminal_actions(amount, config.cogs_of(amount), 0.5,
                                   can_ship=True, p_settles_late=0.25)
        assert v.best()[1] > v.escalate


def test_the_best_action_depends_on_the_order_value():
    small = value_terminal_actions(2499, config.cogs_of(2499), 0.5, True, 0.25)
    large = value_terminal_actions(349900, config.cogs_of(349900), 0.5, True, 0.25)
    assert small.best()[0] == "ship"
    assert large.best()[0] == "close"


def test_certainty_makes_shipping_dominant():
    v = value_terminal_actions(29900, config.cogs_of(29900), 1.0, True, 0.0)
    assert v.best()[0] == "ship"


# --- the shield ------------------------------------------------------------

def test_expected_shield_permits_a_bet_that_pays():
    """It cannot object to positive expected value, and says so."""
    shield = Shield(True, criterion="expected")
    v = value_terminal_actions(29900, config.cogs_of(29900), 0.72, True, 0.25)
    assert v.ship > 0
    assert shield.allows("ship", v, worst_case=-config.cogs_of(29900))


def test_downside_shield_refuses_the_same_bet():
    shield = Shield(True, criterion="downside")
    v = value_terminal_actions(29900, config.cogs_of(29900), 0.72, True, 0.25)
    assert not shield.allows("ship", v, worst_case=-config.cogs_of(29900))


def test_shield_redirects_to_information_rather_than_vetoing(corpus, prior):
    """A veto turns a gambler into a policy that never acts."""
    case = next(c for c in corpus.cases if c.archetype == "pending_settle")
    wrapped = Shielded(OptimisticPolicy(), prior)
    env, _ = run_episode(wrapped, case, FaultProfile(), 0)
    tools = [r.tool for r in env.transcript]
    assert wrapped.blocks > 0
    assert "probe_processor" in tools


def test_shield_cuts_premature_action(corpus, prior):
    bare = evaluate([OptimisticPolicy()], corpus, profile=FaultProfile(), seeds=(0,))
    wrapped_policy = Shielded(OptimisticPolicy(), prior)
    wrapped_policy.name = "shielded"
    shielded = evaluate([wrapped_policy], corpus, profile=FaultProfile(), seeds=(0,))
    assert (summarize(shielded, "shielded").premature_rate
            < summarize(bare, "optimistic").premature_rate)


# --- the planner -----------------------------------------------------------

def test_planner_beats_the_gate_and_the_difference_excludes_zero(grades, corpus):
    """The paper's central claim, as a test.

    A paired resample, because the two policies face identical tasks and their
    marginal intervals overlap almost completely.
    """
    by: dict[str, list] = {}
    for g in grades:
        by.setdefault(g.policy, []).append(g)
    pair_of = {}
    for a, b in corpus.twin_pairs:
        pair_of[a.task_id] = a.task_id
        pair_of[b.task_id] = a.task_id
    d = paired_difference(by["planner"], by["transactional"], mean_gap,
                          pair_of=pair_of, replicates=1500)
    assert d.point < 0
    assert d.high < 0, f"difference spans zero: [{d.low}, {d.high}]"


def test_planner_never_ships_on_an_unverified_replacement(corpus, prior):
    """The premature action the planner itself once committed.

    An earlier version shipped as soon as a replacement capture was submitted,
    which gave away the cost of goods on every unrecoverable failure.
    """
    for case in [c for c in corpus.cases if c.archetype == "pending_fail_hard"][:12]:
        env, _ = run_episode(FinalityAwarePlanner(prior), case, FaultProfile(), 0)
        assert not env.shipped, case.task_id


def test_planner_stays_inside_the_tool_schema(corpus, prior):
    from finalitybench.env import TOOL_SCHEMA

    for case in corpus.cases[:20]:
        env, _ = run_episode(FinalityAwarePlanner(prior), case, FaultProfile(), 0)
        for rec in env.transcript:
            assert rec.tool in TOOL_SCHEMA
            assert "error" not in rec.result


def test_a_wrong_prior_makes_the_planner_worse(corpus):
    """The fitted belief is doing work, not decoration."""
    wrong = FinalityPrior([100] * 300, 0.95, "wrong", [(100, True)] * 300)
    good = FinalityPrior.fit(corpus)
    sample = corpus.cases[:120]
    from finalitybench.tasks import Corpus

    subset = Corpus(corpus.split, corpus.master_seed)
    subset.cases = sample
    g = evaluate([FinalityAwarePlanner(good)], subset, profile=FaultProfile(), seeds=(0,))
    bad_planner = FinalityAwarePlanner(wrong)
    bad_planner.name = "bad"
    b = evaluate([bad_planner], subset, profile=FaultProfile(), seeds=(0,))
    assert summarize(b, "bad").mean_excess > summarize(g, "planner").mean_excess
