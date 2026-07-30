"""Tests for app/domain/workout/rules/context.py."""

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from app.domain.rules.context import RuleContext
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.workout.rules.context import ProgressiveOverloadRuleContext, WorkoutSessionSummary
from app.domain.workout_session.enums import SessionStatus
from tests.domain.workout.rules.factories import a_session_context, a_summary, an_exercise_set

# --- WorkoutSessionSummary.from_session_context() ---


@pytest.mark.unit
def test_from_session_context_computes_total_volume_and_average_load() -> None:
    session = a_session_context(
        sets=[
            an_exercise_set(weight=100.0, reps=5),
            an_exercise_set(set_number=2, weight=100.0, reps=5),
            an_exercise_set(set_number=3, weight=80.0, reps=8),
        ]
    )

    summary = WorkoutSessionSummary.from_session_context(session)

    assert summary.total_volume == pytest.approx(100 * 5 + 100 * 5 + 80 * 8)
    assert summary.average_load == pytest.approx((100.0 + 100.0 + 80.0) / 3)
    assert summary.logged_set_count == 3
    assert summary.session_date == session.session_date


@pytest.mark.unit
def test_from_session_context_with_no_sets_has_zero_volume_and_no_load() -> None:
    session = a_session_context(sets=[])
    summary = WorkoutSessionSummary.from_session_context(session)
    assert summary.total_volume == 0.0
    assert summary.average_load is None
    assert summary.logged_set_count == 0


@pytest.mark.unit
def test_from_session_context_counts_a_zero_weight_bodyweight_set() -> None:
    session = a_session_context(sets=[an_exercise_set(weight=0.0, reps=10)])
    summary = WorkoutSessionSummary.from_session_context(session)
    assert summary.total_volume == 0.0
    assert summary.average_load == 0.0
    assert summary.logged_set_count == 1


@pytest.mark.unit
def test_from_session_context_rejects_a_non_completed_session() -> None:
    session = a_session_context(status=SessionStatus.ACTIVE)
    with pytest.raises(DomainInvariantViolationError, match="Completed"):
        WorkoutSessionSummary.from_session_context(session)


@pytest.mark.unit
def test_summary_is_immutable() -> None:
    summary = a_summary()
    with pytest.raises(FrozenInstanceError):
        summary.total_volume = 500.0  # type: ignore[misc]


# --- ProgressiveOverloadRuleContext ---


@pytest.mark.unit
def test_is_a_rule_context() -> None:
    assert isinstance(ProgressiveOverloadRuleContext(sessions=()), RuleContext)


@pytest.mark.unit
def test_direct_construction_trusts_the_given_order() -> None:
    later = a_summary(session_date=date(2026, 2, 1))
    earlier = a_summary(session_date=date(2026, 1, 1))
    context = ProgressiveOverloadRuleContext(sessions=(later, earlier))
    assert context.sessions == (later, earlier)


@pytest.mark.unit
def test_is_immutable() -> None:
    context = ProgressiveOverloadRuleContext(sessions=())
    with pytest.raises(FrozenInstanceError):
        context.sessions = (a_summary(),)  # type: ignore[misc]


# --- from_session_contexts() ---


@pytest.mark.unit
def test_from_session_contexts_sorts_chronologically() -> None:
    later_session = a_session_context(session_date=date(2026, 2, 1))
    earlier_session = a_session_context(session_date=date(2026, 1, 1))

    context = ProgressiveOverloadRuleContext.from_session_contexts([later_session, earlier_session])

    assert [summary.session_date.value for summary in context.sessions] == [
        date(2026, 1, 1),
        date(2026, 2, 1),
    ]


@pytest.mark.unit
def test_from_session_contexts_filters_out_non_completed_sessions() -> None:
    completed = a_session_context(session_date=date(2026, 1, 1), status=SessionStatus.COMPLETED)
    planned = a_session_context(session_date=date(2026, 1, 2), status=SessionStatus.PLANNED)
    active = a_session_context(session_date=date(2026, 1, 3), status=SessionStatus.ACTIVE)
    abandoned = a_session_context(session_date=date(2026, 1, 4), status=SessionStatus.ABANDONED)

    context = ProgressiveOverloadRuleContext.from_session_contexts(
        [completed, planned, active, abandoned]
    )

    assert len(context.sessions) == 1
    assert context.sessions[0].session_date.value == date(2026, 1, 1)


@pytest.mark.unit
def test_from_session_contexts_with_no_sessions_is_empty() -> None:
    context = ProgressiveOverloadRuleContext.from_session_contexts([])
    assert context.sessions == ()


@pytest.mark.unit
def test_from_session_contexts_does_not_reflect_a_later_mutated_list() -> None:
    sessions = [a_session_context(session_date=date(2026, 1, 1))]
    context = ProgressiveOverloadRuleContext.from_session_contexts(sessions)

    sessions.append(a_session_context(session_date=date(2026, 1, 2)))

    assert len(context.sessions) == 1
