"""Tests for
app/application/progress/handlers/update_body_composition_handler.py."""

import pytest

from app.application.progress.commands.update_body_composition import (
    UpdateBodyCompositionCommand,
)
from app.application.progress.handlers.update_body_composition_handler import (
    UpdateBodyCompositionHandler,
)
from app.domain.progress.identifiers import ProgressId
from app.domain.progress.value_objects import BodyFatPercentage, BodyWeight, MuscleMass
from app.domain.user.identifiers import UserId
from tests.application.progress.factories import (
    FakeProgressRepository,
    FakeUnitOfWork,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_fixed_clock,
    a_recorded_progress,
)


@pytest.mark.unit
def test_replaces_given_fields_and_returns_the_progress_id() -> None:
    progress = a_recorded_progress()
    uow = FakeUnitOfWork(records=FakeProgressRepository({progress.id: progress}))
    handler = UpdateBodyCompositionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(
        UpdateBodyCompositionCommand(
            progress_id=progress.id,
            requester_id=progress.user_id,
            body_weight=BodyWeight(80.0),
            body_fat_percentage=BodyFatPercentage(20.0),
        )
    )

    assert result.success is True
    assert result.value == progress.id
    assert progress.body_weight == BodyWeight(80.0)
    assert progress.body_fat_percentage == BodyFatPercentage(20.0)


@pytest.mark.unit
def test_leaves_fields_unset_in_the_command_unchanged() -> None:
    progress = a_recorded_progress()
    progress.update_body_composition(
        body_weight=BodyWeight(80.0), muscle_mass=MuscleMass(35.0), clock=a_fixed_clock()
    )
    progress.pull_domain_events()
    uow = FakeUnitOfWork(records=FakeProgressRepository({progress.id: progress}))
    handler = UpdateBodyCompositionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    handler.handle(
        UpdateBodyCompositionCommand(
            progress_id=progress.id,
            requester_id=progress.user_id,
            body_fat_percentage=BodyFatPercentage(18.0),
        )
    )

    assert progress.body_weight == BodyWeight(80.0)
    assert progress.muscle_mass == MuscleMass(35.0)
    assert progress.body_fat_percentage == BodyFatPercentage(18.0)


@pytest.mark.unit
def test_commits_and_dispatches_body_composition_updated_after_commit() -> None:
    progress = a_recorded_progress()
    uow = FakeUnitOfWork(records=FakeProgressRepository({progress.id: progress}))
    dispatcher = RecordingDispatcher()
    handler = UpdateBodyCompositionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(
        UpdateBodyCompositionCommand(
            progress_id=progress.id, requester_id=progress.user_id, body_weight=BodyWeight(80.0)
        )
    )

    assert uow.committed is True
    kinds = {type(event).__name__ for event in dispatcher.dispatched}
    assert "BodyCompositionUpdated" in kinds


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    progress = a_recorded_progress()
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(
        records=FakeProgressRepository({progress.id: progress}), call_order=call_order
    )
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = UpdateBodyCompositionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(
        UpdateBodyCompositionCommand(
            progress_id=progress.id, requester_id=progress.user_id, body_weight=BodyWeight(80.0)
        )
    )

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_surfaces_consistency_warning_since_only_one_entry_exists() -> None:
    progress = a_recorded_progress()
    uow = FakeUnitOfWork(records=FakeProgressRepository({progress.id: progress}))
    handler = UpdateBodyCompositionHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(
        UpdateBodyCompositionCommand(
            progress_id=progress.id, requester_id=progress.user_id, body_weight=BodyWeight(80.0)
        )
    )

    assert result.success is True
    assert any("log progress more regularly" in warning.lower() for warning in result.warnings)


@pytest.mark.unit
def test_a_missing_progress_record_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = UpdateBodyCompositionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())
    missing_id = ProgressId.generate()

    result = handler.handle(
        UpdateBodyCompositionCommand(
            progress_id=missing_id, requester_id=UserId.generate(), body_weight=BodyWeight(80.0)
        )
    )

    assert result.success is False
    assert str(missing_id) in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork(records=FakeProgressRepository(fail_on_get=True))
    dispatcher = RecordingDispatcher()
    handler = UpdateBodyCompositionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        UpdateBodyCompositionCommand(
            progress_id=ProgressId.generate(),
            requester_id=UserId.generate(),
            body_weight=BodyWeight(80.0),
        )
    )

    assert result.success is False
    assert uow.rolled_back is True


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    progress = a_recorded_progress()
    uow = FakeUnitOfWork(
        records=FakeProgressRepository({progress.id: progress}), fail_on_commit=True
    )
    dispatcher = RecordingDispatcher()
    handler = UpdateBodyCompositionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        UpdateBodyCompositionCommand(
            progress_id=progress.id, requester_id=progress.user_id, body_weight=BodyWeight(80.0)
        )
    )

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_non_owner_requester_is_denied_and_rolls_back() -> None:
    progress = a_recorded_progress()
    uow = FakeUnitOfWork(records=FakeProgressRepository({progress.id: progress}))
    dispatcher = RecordingDispatcher()
    handler = UpdateBodyCompositionHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        UpdateBodyCompositionCommand(
            progress_id=progress.id, requester_id=UserId.generate(), body_weight=BodyWeight(80.0)
        )
    )

    assert result.success is False
    assert result.forbidden is True
    assert result.value is None
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []
