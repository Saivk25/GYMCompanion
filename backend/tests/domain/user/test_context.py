"""Tests for app/domain/user/context.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.domain.shared_kernel.clock import FixedClock
from app.domain.user.context import UserContext
from app.domain.user.enums import AccountStatus, ExperienceLevel
from app.domain.user.identifiers import UserId
from app.domain.user.user import User
from app.domain.user.value_objects import AuthMethod, Locale, Timezone, UserPreferences, UserProfile
from tests.domain.user.factories import a_fixed_clock


@pytest.mark.unit
def test_from_user_snapshots_every_relevant_field() -> None:
    clock: FixedClock = a_fixed_clock()
    user = User.register(
        user_id=UserId.generate(),
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        auth_method=AuthMethod("webauthn_passkey"),
        clock=clock,
    )
    profile = UserProfile(
        height_cm=178.0, birth_year=1998, experience_level=ExperienceLevel.BEGINNER
    )
    user.update_profile(profile, clock=clock)
    preferences = UserPreferences(biometric_app_lock_enabled=True)
    user.update_preferences(preferences)

    context = UserContext.from_user(user)

    assert context.user_id == user.id
    assert context.account_status == AccountStatus.INVITED
    assert context.locale == Locale("en")
    assert context.timezone == Timezone("UTC")
    assert context.profile == profile
    assert context.preferences == preferences


@pytest.mark.unit
def test_is_immutable() -> None:
    clock: FixedClock = a_fixed_clock()
    user = User.register(
        user_id=UserId.generate(),
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        auth_method=AuthMethod("webauthn_passkey"),
        clock=clock,
    )
    context = UserContext.from_user(user)
    with pytest.raises(FrozenInstanceError):
        context.locale = Locale("fr")  # type: ignore[misc]


@pytest.mark.unit
def test_does_not_reflect_later_mutations_of_the_source_user() -> None:
    """A snapshot is a snapshot — the whole point is that it stays exactly
    as it was even after the live aggregate moves on."""
    clock: FixedClock = a_fixed_clock()
    user = User.register(
        user_id=UserId.generate(),
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        auth_method=AuthMethod("webauthn_passkey"),
        clock=clock,
    )
    context = UserContext.from_user(user)

    user.activate()
    user.suspend()

    assert context.account_status == AccountStatus.INVITED
    assert user.account_status == AccountStatus.SUSPENDED
