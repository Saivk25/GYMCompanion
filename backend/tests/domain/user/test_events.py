"""Tests for app/domain/user/events.py.

Immutability, `event_id` auto-generation, and `occurred_at` timezone
enforcement are `DomainEvent` base behavior, already fully covered by
`tests/domain/shared_kernel/test_events.py`. This file only proves each
User-specific event carries the fields it's supposed to.
"""

from datetime import datetime, timezone

import pytest

from app.domain.user.enums import ExperienceLevel
from app.domain.user.events import UserProfileUpdated, UserRegistered
from app.domain.user.identifiers import UserId
from app.domain.user.value_objects import Locale, Timezone, UserProfile


@pytest.mark.unit
def test_user_registered_carries_locale_and_timezone() -> None:
    user_id = UserId.generate()
    event = UserRegistered(
        occurred_at=datetime.now(timezone.utc),
        user_id=user_id,
        locale=Locale("en"),
        timezone=Timezone("UTC"),
    )
    assert event.user_id == user_id
    assert event.locale == Locale("en")
    assert event.timezone == Timezone("UTC")


@pytest.mark.unit
def test_user_profile_updated_carries_the_full_new_profile() -> None:
    user_id = UserId.generate()
    profile = UserProfile(
        height_cm=178.0, birth_year=1998, experience_level=ExperienceLevel.BEGINNER
    )
    event = UserProfileUpdated(
        occurred_at=datetime.now(timezone.utc),
        user_id=user_id,
        profile=profile,
    )
    assert event.user_id == user_id
    assert event.profile == profile
