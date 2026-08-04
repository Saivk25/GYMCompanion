"""`UserSqlRepository`: the SQLAlchemy-backed implementation of
`app.domain.user.repository.UserRepository`.

Tenant scoping note (see `app/infra/database.py`'s module docstring and the
users-table migration's for the full RLS background): `users` is the tenant
root — a `User`'s own id *is* the tenant boundary, unlike every other
repository in this package. That means, uniquely among these repositories,
`get()` can safely open `tenant_scope(session, str(entity_id))` itself using
only the id it was given, with no chicken-and-egg problem (every other
tenant-scoped aggregate's `get()` cannot do this — see
`workout_repository.py`'s module docstring for why). `add()`/`remove()`
similarly scope from `aggregate.id` directly.
"""

from __future__ import annotations

from app.domain.exercise.value_objects import EquipmentRequirement
from app.domain.user.enums import AccountStatus, BiologicalSex, ExperienceLevel
from app.domain.user.identifiers import UserId
from app.domain.user.repository import UserRepository
from app.domain.user.user import User
from app.domain.user.value_objects import (
    AuthMethod,
    Locale,
    QuietHours,
    Timezone,
    UserPreferences,
    UserProfile,
)
from app.infra.database import tenant_scope
from app.infra.models.user import UserAccount
from app.infra.repositories._tracking import TrackingRepository


class UserSqlRepository(UserRepository, TrackingRepository[User, UserId, UserAccount]):
    """Postgres-backed `UserRepository`. See the module docstring for the
    tenant-scoping shape specific to this one repository.
    """

    def get(self, entity_id: UserId) -> User | None:
        with tenant_scope(self._session, str(entity_id)):
            row = self._session.get(UserAccount, entity_id.value)
        if row is None:
            return None
        user = _to_domain(row)
        self._track(entity_id, user, row)
        return user

    def add(self, aggregate: User) -> None:
        with tenant_scope(self._session, str(aggregate.id)):
            row = UserAccount(user_id=aggregate.id.value)
            self._apply_to_row(aggregate, row)
            self._session.add(row)
        self._track(aggregate.id, aggregate, row)

    def remove(self, aggregate: User) -> None:
        with tenant_scope(self._session, str(aggregate.id)):
            row = self._session.get(UserAccount, aggregate.id.value)
            if row is not None:
                self._session.delete(row)
        self._untrack(aggregate.id)

    def _apply_to_row(self, aggregate: User, row: UserAccount) -> None:
        row.locale = aggregate.locale.value
        row.timezone = aggregate.timezone.value
        row.account_status = aggregate.account_status.value
        row.auth_method = aggregate.auth_method.value

        profile = aggregate.profile
        row.height_cm = profile.height_cm if profile is not None else None
        row.birth_year = profile.birth_year if profile is not None else None
        row.experience_level = profile.experience_level.value if profile is not None else None
        row.biological_sex = (
            profile.sex.value if profile is not None and profile.sex is not None else None
        )

        preferences = aggregate.preferences
        quiet_hours = preferences.quiet_hours
        row.quiet_hours_starts_at = quiet_hours.starts_at if quiet_hours is not None else None
        row.quiet_hours_ends_at = quiet_hours.ends_at if quiet_hours is not None else None
        row.biometric_app_lock_enabled = preferences.biometric_app_lock_enabled
        row.available_equipment = sorted(item.value for item in preferences.available_equipment)


def _to_domain(row: UserAccount) -> User:
    profile: UserProfile | None = None
    if (
        row.height_cm is not None
        and row.birth_year is not None
        and row.experience_level is not None
    ):
        profile = UserProfile(
            height_cm=row.height_cm,
            birth_year=row.birth_year,
            experience_level=ExperienceLevel(row.experience_level),
            sex=BiologicalSex(row.biological_sex) if row.biological_sex is not None else None,
        )

    quiet_hours: QuietHours | None = None
    if row.quiet_hours_starts_at is not None and row.quiet_hours_ends_at is not None:
        quiet_hours = QuietHours(
            starts_at=row.quiet_hours_starts_at, ends_at=row.quiet_hours_ends_at
        )

    preferences = UserPreferences(
        quiet_hours=quiet_hours,
        biometric_app_lock_enabled=row.biometric_app_lock_enabled,
        available_equipment=frozenset(
            EquipmentRequirement(value) for value in row.available_equipment
        ),
    )

    return User(
        UserId(row.user_id),
        created_at=row.created_at,
        locale=Locale(row.locale),
        timezone=Timezone(row.timezone),
        auth_method=AuthMethod(row.auth_method),
        account_status=AccountStatus(row.account_status),
        profile=profile,
        preferences=preferences,
    )
