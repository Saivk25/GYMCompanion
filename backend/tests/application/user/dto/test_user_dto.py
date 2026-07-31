"""Tests for app/application/user/dto/user_dto.py."""

from dataclasses import FrozenInstanceError

import pytest

from app.application.user.dto.user_dto import UserDTO
from app.domain.user.enums import AccountStatus, ExperienceLevel
from app.domain.user.identifiers import UserId
from app.domain.user.user import User
from app.domain.user.value_objects import AuthMethod, Locale, Timezone, UserProfile
from tests.application.user.factories import a_fixed_clock


def _a_registered_user() -> User:
    return User.register(
        user_id=UserId.generate(),
        locale=Locale("en"),
        timezone=Timezone("UTC"),
        auth_method=AuthMethod("webauthn_passkey"),
        clock=a_fixed_clock(),
    )


@pytest.mark.unit
def test_from_user_maps_every_field() -> None:
    user = _a_registered_user()

    dto = UserDTO.from_user(user)

    assert dto.user_id == user.id
    assert dto.account_status == AccountStatus.INVITED
    assert dto.created_at == user.created_at
    assert dto.locale == Locale("en")
    assert dto.timezone == Timezone("UTC")
    assert dto.auth_method == AuthMethod("webauthn_passkey")
    assert dto.profile is None
    assert dto.preferences == user.preferences
    assert dto.has_complete_profile is False


@pytest.mark.unit
def test_from_user_reflects_a_completed_profile() -> None:
    user = _a_registered_user()
    profile = UserProfile(
        height_cm=178.0, birth_year=1998, experience_level=ExperienceLevel.BEGINNER
    )
    user.update_profile(profile, clock=a_fixed_clock())

    dto = UserDTO.from_user(user)

    assert dto.profile == profile
    assert dto.has_complete_profile is True


@pytest.mark.unit
def test_user_dto_is_immutable() -> None:
    dto = UserDTO.from_user(_a_registered_user())
    with pytest.raises(FrozenInstanceError):
        dto.account_status = AccountStatus.ACTIVE  # type: ignore[misc]
