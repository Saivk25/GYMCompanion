"""Tests for app/domain/user/value_objects.py."""

from dataclasses import FrozenInstanceError
from datetime import time

import pytest

from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.user.enums import BiologicalSex, ExperienceLevel
from app.domain.user.value_objects import (
    AuthMethod,
    Locale,
    QuietHours,
    Timezone,
    UserPreferences,
    UserProfile,
)

# --- Locale ---


@pytest.mark.unit
@pytest.mark.parametrize("value", ["en", "en-US", "hi-IN", "fr"])
def test_locale_accepts_well_formed_tags(value: str) -> None:
    assert Locale(value).value == value


@pytest.mark.unit
@pytest.mark.parametrize("value", ["", "english", "EN", "en_US", "en-us"])
def test_locale_rejects_malformed_tags(value: str) -> None:
    with pytest.raises(DomainInvariantViolationError):
        Locale(value)


# --- Timezone ---


@pytest.mark.unit
@pytest.mark.parametrize("value", ["UTC", "Asia/Kolkata", "America/New_York"])
def test_timezone_accepts_real_iana_names(value: str) -> None:
    assert Timezone(value).value == value


@pytest.mark.unit
def test_timezone_rejects_empty_string() -> None:
    with pytest.raises(DomainInvariantViolationError, match="timezone"):
        Timezone("")


@pytest.mark.unit
def test_timezone_rejects_a_name_not_in_the_iana_database() -> None:
    with pytest.raises(DomainInvariantViolationError, match="valid IANA time zone"):
        Timezone("Not/ARealZone")


# --- AuthMethod ---


@pytest.mark.unit
def test_auth_method_accepts_a_non_empty_value() -> None:
    assert AuthMethod("webauthn_passkey").value == "webauthn_passkey"


@pytest.mark.unit
def test_auth_method_rejects_blank_values() -> None:
    with pytest.raises(DomainInvariantViolationError, match="auth_method must not be empty"):
        AuthMethod("   ")


# --- UserProfile ---


@pytest.mark.unit
def test_user_profile_accepts_valid_fields() -> None:
    profile = UserProfile(
        height_cm=178.0,
        birth_year=1998,
        experience_level=ExperienceLevel.INTERMEDIATE,
        sex=BiologicalSex.MALE,
    )
    assert profile.height_cm == 178.0
    assert profile.birth_year == 1998
    assert profile.experience_level is ExperienceLevel.INTERMEDIATE
    assert profile.sex is BiologicalSex.MALE


@pytest.mark.unit
def test_user_profile_sex_defaults_to_none() -> None:
    """sex_optional per the Bible — declining to disclose is a first-class,
    default outcome, not an edge case."""
    profile = UserProfile(
        height_cm=178.0, birth_year=1998, experience_level=ExperienceLevel.BEGINNER
    )
    assert profile.sex is None


@pytest.mark.unit
@pytest.mark.parametrize("height_cm", [0, -10.0])
def test_user_profile_rejects_non_positive_height(height_cm: float) -> None:
    with pytest.raises(DomainInvariantViolationError, match="height_cm must be positive"):
        UserProfile(height_cm=height_cm, birth_year=1998, experience_level=ExperienceLevel.BEGINNER)


@pytest.mark.unit
def test_user_profile_rejects_an_implausibly_tall_height() -> None:
    with pytest.raises(DomainInvariantViolationError, match="plausible human height"):
        UserProfile(height_cm=301.0, birth_year=1998, experience_level=ExperienceLevel.BEGINNER)


@pytest.mark.unit
@pytest.mark.parametrize("birth_year", [1899, 2101])
def test_user_profile_rejects_implausible_birth_years(birth_year: int) -> None:
    with pytest.raises(DomainInvariantViolationError, match="birth_year must be between"):
        UserProfile(
            height_cm=178.0, birth_year=birth_year, experience_level=ExperienceLevel.BEGINNER
        )


@pytest.mark.unit
def test_user_profile_is_immutable() -> None:
    profile = UserProfile(
        height_cm=178.0, birth_year=1998, experience_level=ExperienceLevel.BEGINNER
    )
    with pytest.raises(FrozenInstanceError):
        profile.height_cm = 180.0  # type: ignore[misc]


# --- QuietHours ---


@pytest.mark.unit
def test_quiet_hours_accepts_a_window_that_wraps_past_midnight() -> None:
    window = QuietHours(starts_at=time(22, 0), ends_at=time(7, 0))
    assert window.starts_at == time(22, 0)
    assert window.ends_at == time(7, 0)


@pytest.mark.unit
def test_quiet_hours_rejects_a_zero_length_window() -> None:
    with pytest.raises(DomainInvariantViolationError, match="must differ"):
        QuietHours(starts_at=time(9, 0), ends_at=time(9, 0))


# --- UserPreferences ---


@pytest.mark.unit
def test_user_preferences_defaults_are_all_valid() -> None:
    preferences = UserPreferences()
    assert preferences.quiet_hours is None
    assert preferences.biometric_app_lock_enabled is False


@pytest.mark.unit
def test_user_preferences_accepts_explicit_values() -> None:
    window = QuietHours(starts_at=time(22, 0), ends_at=time(7, 0))
    preferences = UserPreferences(quiet_hours=window, biometric_app_lock_enabled=True)
    assert preferences.quiet_hours == window
    assert preferences.biometric_app_lock_enabled is True
