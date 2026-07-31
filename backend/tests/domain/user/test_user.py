"""Tests for app/domain/user/user.py."""

from datetime import datetime, timezone

import pytest

from app.domain.exercise.value_objects import EquipmentRequirement
from app.domain.shared_kernel.clock import Clock
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.user.enums import AccountStatus, ExperienceLevel
from app.domain.user.events import UserProfileUpdated, UserRegistered
from app.domain.user.identifiers import UserId
from app.domain.user.user import User
from app.domain.user.value_objects import AuthMethod, Locale, Timezone, UserPreferences, UserProfile
from tests.domain.user.factories import a_fixed_clock


def _a_registered_user(*, clock: Clock | None = None) -> User:
    return User.register(
        user_id=UserId.generate(),
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        auth_method=AuthMethod("webauthn_passkey"),
        clock=clock or a_fixed_clock(),
    )


# --- register() ---


@pytest.mark.unit
def test_register_starts_in_the_invited_state() -> None:
    user = _a_registered_user()
    assert user.account_status == AccountStatus.INVITED


@pytest.mark.unit
def test_register_stamps_created_at_from_the_clock() -> None:
    clock = a_fixed_clock()
    user = _a_registered_user(clock=clock)
    assert user.created_at == clock.now()


@pytest.mark.unit
def test_register_exposes_the_fields_it_was_given() -> None:
    user_id = UserId.generate()
    user = User.register(
        user_id=user_id,
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        auth_method=AuthMethod("webauthn_passkey"),
        clock=a_fixed_clock(),
    )
    assert user.id == user_id
    assert user.locale == Locale("en")
    assert user.timezone == Timezone("UTC")
    assert user.auth_method == AuthMethod("webauthn_passkey")


@pytest.mark.unit
def test_register_starts_with_no_profile_and_default_preferences() -> None:
    user = _a_registered_user()
    assert user.profile is None
    assert user.has_complete_profile is False
    assert user.preferences == UserPreferences()


@pytest.mark.unit
def test_register_records_a_user_registered_event() -> None:
    clock = a_fixed_clock()
    user_id = UserId.generate()
    user = User.register(
        user_id=user_id,
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        auth_method=AuthMethod("webauthn_passkey"),
        clock=clock,
    )

    events = user.pull_domain_events()

    assert len(events) == 1
    assert isinstance(events[0], UserRegistered)
    assert events[0].user_id == user_id
    assert events[0].locale == Locale("en")
    assert events[0].timezone == Timezone("UTC")
    assert events[0].occurred_at == clock.now()


@pytest.mark.unit
def test_register_generates_a_distinct_user_each_time() -> None:
    assert _a_registered_user().id != _a_registered_user().id


# --- update_profile() ---


@pytest.mark.unit
def test_update_profile_replaces_the_profile_and_flips_completeness() -> None:
    user = _a_registered_user()
    profile = UserProfile(
        height_cm=178.0, birth_year=1998, experience_level=ExperienceLevel.BEGINNER
    )

    user.update_profile(profile, clock=a_fixed_clock())

    assert user.profile == profile
    assert user.has_complete_profile is True


@pytest.mark.unit
def test_update_profile_records_a_user_profile_updated_event() -> None:
    user = _a_registered_user()
    user.pull_domain_events()  # drain the UserRegistered event from setup
    clock = a_fixed_clock()
    profile = UserProfile(
        height_cm=178.0, birth_year=1998, experience_level=ExperienceLevel.BEGINNER
    )

    user.update_profile(profile, clock=clock)

    events = user.pull_domain_events()
    assert len(events) == 1
    assert isinstance(events[0], UserProfileUpdated)
    assert events[0].user_id == user.id
    assert events[0].profile == profile
    assert events[0].occurred_at == clock.now()


@pytest.mark.unit
def test_update_profile_is_rejected_after_deletion() -> None:
    user = _a_registered_user()
    user.delete()
    profile = UserProfile(
        height_cm=178.0, birth_year=1998, experience_level=ExperienceLevel.BEGINNER
    )

    with pytest.raises(DomainInvariantViolationError, match="cannot modify a user"):
        user.update_profile(profile, clock=a_fixed_clock())


# --- update_preferences() ---


@pytest.mark.unit
def test_update_preferences_replaces_preferences_without_an_event() -> None:
    user = _a_registered_user()
    user.pull_domain_events()  # drain the UserRegistered event from setup
    new_preferences = UserPreferences(biometric_app_lock_enabled=True)

    user.update_preferences(new_preferences)

    assert user.preferences == new_preferences
    assert user.pull_domain_events() == []


@pytest.mark.unit
def test_update_preferences_is_rejected_after_deletion() -> None:
    user = _a_registered_user()
    user.delete()

    with pytest.raises(DomainInvariantViolationError, match="cannot modify a user"):
        user.update_preferences(UserPreferences(biometric_app_lock_enabled=True))


# --- update_equipment() ---


@pytest.mark.unit
def test_update_equipment_replaces_available_equipment_without_an_event() -> None:
    user = _a_registered_user()
    user.pull_domain_events()  # drain the UserRegistered event from setup
    equipment = frozenset({EquipmentRequirement("barbell"), EquipmentRequirement("dumbbell")})

    user.update_equipment(equipment)

    assert user.preferences.available_equipment == equipment
    assert user.pull_domain_events() == []


@pytest.mark.unit
def test_update_equipment_preserves_the_rest_of_preferences() -> None:
    user = _a_registered_user()
    user.update_preferences(UserPreferences(biometric_app_lock_enabled=True))

    user.update_equipment(frozenset({EquipmentRequirement("kettlebell")}))

    assert user.preferences.biometric_app_lock_enabled is True
    assert user.preferences.available_equipment == frozenset({EquipmentRequirement("kettlebell")})


@pytest.mark.unit
def test_update_equipment_is_rejected_after_deletion() -> None:
    user = _a_registered_user()
    user.delete()

    with pytest.raises(DomainInvariantViolationError, match="cannot modify a user"):
        user.update_equipment(frozenset({EquipmentRequirement("barbell")}))


# --- account_status state machine ---


@pytest.mark.unit
def test_activate_moves_invited_to_active() -> None:
    user = _a_registered_user()
    user.activate()
    assert user.account_status == AccountStatus.ACTIVE


@pytest.mark.unit
def test_activate_is_rejected_when_not_invited() -> None:
    user = _a_registered_user()
    user.activate()
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        user.activate()


@pytest.mark.unit
def test_suspend_moves_active_to_suspended() -> None:
    user = _a_registered_user()
    user.activate()
    user.suspend()
    assert user.account_status == AccountStatus.SUSPENDED


@pytest.mark.unit
def test_suspend_is_rejected_when_not_active() -> None:
    user = _a_registered_user()
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        user.suspend()


@pytest.mark.unit
def test_activate_moves_suspended_back_to_active() -> None:
    """The Bible's one documented exception to one-directional transitions —
    the same `activate()` used for Invited -> Active also covers this."""
    user = _a_registered_user()
    user.activate()
    user.suspend()
    user.activate()
    assert user.account_status == AccountStatus.ACTIVE


@pytest.mark.unit
def test_activate_is_rejected_when_deleted() -> None:
    """Regression guard for the bug this test caught during development:
    `activate()` must stay rejected from every state that isn't Invited or
    Suspended, not just from Active (see `test_activate_is_rejected_when_not_invited`)."""
    user = _a_registered_user()
    user.delete()
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        user.activate()


@pytest.mark.unit
@pytest.mark.parametrize("prior_transition", ["none", "activate", "activate_suspend"])
def test_delete_is_reachable_from_every_non_terminal_state(prior_transition: str) -> None:
    """The user's delete right must be reachable from Invited, Active, and
    Suspended alike (Bible Section 4.1, Table 4, "Ownership")."""
    user = _a_registered_user()
    if prior_transition in ("activate", "activate_suspend"):
        user.activate()
    if prior_transition == "activate_suspend":
        user.suspend()

    user.delete()

    assert user.account_status == AccountStatus.DELETED


@pytest.mark.unit
def test_delete_is_rejected_when_already_deleted() -> None:
    user = _a_registered_user()
    user.delete()
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        user.delete()


@pytest.mark.unit
def test_delete_is_blocked_by_an_unacknowledged_open_escalation() -> None:
    user = _a_registered_user()
    with pytest.raises(DomainInvariantViolationError, match="unresolved EscalationCase"):
        user.delete(has_unresolved_escalation=True)
    assert user.account_status == AccountStatus.INVITED


@pytest.mark.unit
def test_delete_succeeds_when_the_open_escalation_is_acknowledged() -> None:
    user = _a_registered_user()
    user.delete(has_unresolved_escalation=True, escalation_acknowledged=True)
    assert user.account_status == AccountStatus.DELETED


@pytest.mark.unit
def test_purge_moves_deleted_to_purged() -> None:
    user = _a_registered_user()
    user.delete()
    user.purge()
    assert user.account_status == AccountStatus.PURGED


@pytest.mark.unit
def test_purge_is_rejected_when_not_deleted() -> None:
    user = _a_registered_user()
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        user.purge()


@pytest.mark.unit
def test_purge_is_terminal() -> None:
    user = _a_registered_user()
    user.delete()
    user.purge()
    with pytest.raises(DomainInvariantViolationError, match="cannot transition"):
        user.purge()


# --- __init__ construction (repository rehydration path) ---


@pytest.mark.unit
def test_constructor_rejects_a_naive_created_at() -> None:
    with pytest.raises(DomainInvariantViolationError, match="timezone-aware"):
        User(
            UserId.generate(),
            created_at=datetime(2026, 1, 1),  # deliberately naive
            locale=Locale("en"),
            timezone=Timezone("UTC"),
            auth_method=AuthMethod("webauthn_passkey"),
        )


@pytest.mark.unit
def test_constructor_rehydrates_an_existing_user_without_raising_an_event() -> None:
    """The path a repository uses to reconstruct a User already in
    storage — re-raising UserRegistered here would be wrong."""
    user = User(
        UserId.generate(),
        created_at=datetime.now(timezone.utc),
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        auth_method=AuthMethod("webauthn_passkey"),
        account_status=AccountStatus.ACTIVE,
    )
    assert user.pull_domain_events() == []
    assert user.account_status == AccountStatus.ACTIVE


@pytest.mark.unit
def test_constructor_accepts_explicit_profile_and_preferences() -> None:
    profile = UserProfile(
        height_cm=178.0, birth_year=1998, experience_level=ExperienceLevel.BEGINNER
    )
    preferences = UserPreferences(biometric_app_lock_enabled=True)
    user = User(
        UserId.generate(),
        created_at=datetime.now(timezone.utc),
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        auth_method=AuthMethod("webauthn_passkey"),
        profile=profile,
        preferences=preferences,
    )
    assert user.profile == profile
    assert user.preferences == preferences
