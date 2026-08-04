"""Tests for
app/application/readiness/handlers/update_recovery_metrics_handler.py."""

import pytest

from app.application.readiness.commands.update_recovery_metrics import (
    UpdateRecoveryMetricsCommand,
)
from app.application.readiness.handlers.update_recovery_metrics_handler import (
    UpdateRecoveryMetricsHandler,
)
from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.value_objects import EnergyLevel, StressLevel
from tests.application.readiness.factories import (
    FakeReadinessRepository,
    FakeUnitOfWork,
    OrderTrackingDispatcher,
    OrderTrackingUnitOfWork,
    RecordingDispatcher,
    a_fixed_clock,
    a_recorded_readiness,
)


@pytest.mark.unit
def test_replaces_given_fields_and_returns_the_readiness_id() -> None:
    readiness = a_recorded_readiness()
    uow = FakeUnitOfWork(entries=FakeReadinessRepository({readiness.id: readiness}))
    handler = UpdateRecoveryMetricsHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(
        UpdateRecoveryMetricsCommand(
            readiness_id=readiness.id, energy_level=EnergyLevel(7), stress_level=StressLevel(3)
        )
    )

    assert result.success is True
    assert result.value == readiness.id
    assert readiness.energy_level == EnergyLevel(7)
    assert readiness.stress_level == StressLevel(3)


@pytest.mark.unit
def test_leaves_fields_unset_in_the_command_unchanged() -> None:
    readiness = a_recorded_readiness()
    readiness.update_recovery_metrics(
        energy_level=EnergyLevel(7), stress_level=StressLevel(3), clock=a_fixed_clock()
    )
    readiness.pull_domain_events()
    uow = FakeUnitOfWork(entries=FakeReadinessRepository({readiness.id: readiness}))
    handler = UpdateRecoveryMetricsHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    handler.handle(
        UpdateRecoveryMetricsCommand(readiness_id=readiness.id, stress_level=StressLevel(5))
    )

    assert readiness.energy_level == EnergyLevel(7)
    assert readiness.stress_level == StressLevel(5)


@pytest.mark.unit
def test_commits_and_dispatches_recovery_metrics_updated_after_commit() -> None:
    readiness = a_recorded_readiness()
    uow = FakeUnitOfWork(entries=FakeReadinessRepository({readiness.id: readiness}))
    dispatcher = RecordingDispatcher()
    handler = UpdateRecoveryMetricsHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(
        UpdateRecoveryMetricsCommand(readiness_id=readiness.id, energy_level=EnergyLevel(7))
    )

    assert uow.committed is True
    kinds = {type(event).__name__ for event in dispatcher.dispatched}
    assert "RecoveryMetricsUpdated" in kinds


@pytest.mark.unit
def test_dispatch_happens_strictly_after_commit() -> None:
    readiness = a_recorded_readiness()
    call_order: list[str] = []
    uow = OrderTrackingUnitOfWork(
        entries=FakeReadinessRepository({readiness.id: readiness}), call_order=call_order
    )
    dispatcher = OrderTrackingDispatcher(call_order)
    handler = UpdateRecoveryMetricsHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    handler.handle(
        UpdateRecoveryMetricsCommand(readiness_id=readiness.id, energy_level=EnergyLevel(7))
    )

    assert call_order == ["commit", "dispatch"]


@pytest.mark.unit
def test_surfaces_a_warning_for_low_energy() -> None:
    readiness = a_recorded_readiness()
    uow = FakeUnitOfWork(entries=FakeReadinessRepository({readiness.id: readiness}))
    handler = UpdateRecoveryMetricsHandler(
        uow=uow, dispatcher=RecordingDispatcher(), clock=a_fixed_clock()
    )

    result = handler.handle(
        UpdateRecoveryMetricsCommand(readiness_id=readiness.id, energy_level=EnergyLevel(2))
    )

    assert result.success is True
    assert len(result.warnings) > 0


@pytest.mark.unit
def test_a_missing_readiness_check_in_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork()
    dispatcher = RecordingDispatcher()
    handler = UpdateRecoveryMetricsHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())
    missing_id = ReadinessId.generate()

    result = handler.handle(
        UpdateRecoveryMetricsCommand(readiness_id=missing_id, energy_level=EnergyLevel(7))
    )

    assert result.success is False
    assert str(missing_id) in result.errors[0]
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []


@pytest.mark.unit
def test_a_repository_get_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    uow = FakeUnitOfWork(entries=FakeReadinessRepository(fail_on_get=True))
    dispatcher = RecordingDispatcher()
    handler = UpdateRecoveryMetricsHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        UpdateRecoveryMetricsCommand(
            readiness_id=ReadinessId.generate(), energy_level=EnergyLevel(7)
        )
    )

    assert result.success is False
    assert uow.rolled_back is True


@pytest.mark.unit
def test_a_commit_failure_is_reported_as_a_failed_result_and_rolls_back() -> None:
    readiness = a_recorded_readiness()
    uow = FakeUnitOfWork(
        entries=FakeReadinessRepository({readiness.id: readiness}), fail_on_commit=True
    )
    dispatcher = RecordingDispatcher()
    handler = UpdateRecoveryMetricsHandler(uow=uow, dispatcher=dispatcher, clock=a_fixed_clock())

    result = handler.handle(
        UpdateRecoveryMetricsCommand(readiness_id=readiness.id, energy_level=EnergyLevel(7))
    )

    assert result.success is False
    assert uow.rolled_back is True
    assert dispatcher.dispatched == []
