"""Immutable value objects owned by the User aggregate.

Every type here is a `ValueObject` subclass (`app.domain.shared_kernel`):
no identity, replaced wholesale on change, validated once at construction
so an instance is either fully valid or doesn't exist. See each class's
docstring for which Domain Model & Decision Engine Bible table it comes
from and, where a field isn't literally named there, the reasoning for
adding it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.domain.exercise.value_objects import EquipmentRequirement
from app.domain.shared_kernel.errors import DomainInvariantViolationError
from app.domain.shared_kernel.validation import ensure, ensure_not_empty, ensure_positive
from app.domain.shared_kernel.value_object import ValueObject
from app.domain.user.enums import BiologicalSex, ExperienceLevel

# A permissive BCP-47-style check (language, optional region subtag), not a
# full RFC 5646 parser — "en", "en-US", "hi-IN". Domain code needs to reject
# obvious garbage ("not a locale"), not fully validate every legal BCP-47
# extension; a real parsing library would be exactly the kind of dependency
# app/domain is not allowed to take on (see test_import_boundaries.py).
_LOCALE_PATTERN = re.compile(r"^[a-z]{2,3}(-[A-Z]{2})?$")

_MAX_PLAUSIBLE_HEIGHT_CM = 300.0
_MIN_PLAUSIBLE_BIRTH_YEAR = 1900
_MAX_PLAUSIBLE_BIRTH_YEAR = 2100


@dataclass(frozen=True)
class Locale(ValueObject):
    """A BCP-47-style language[-region] tag, e.g. `Locale("en")` or
    `Locale("hi-IN")`. One of `User`'s key attributes (Bible Section 4.1,
    Table 4).
    """

    value: str

    def __post_init__(self) -> None:
        ensure_not_empty(self.value, "locale")
        ensure(
            _LOCALE_PATTERN.fullmatch(self.value) is not None,
            f"locale must look like 'en' or 'en-US', got {self.value!r}",
        )


@dataclass(frozen=True)
class Timezone(ValueObject):
    """An IANA time zone name, e.g. `Timezone("Asia/Kolkata")`. One of
    `User`'s key attributes (Bible Section 4.1, Table 4).

    Validated against the real IANA database via the stdlib `zoneinfo`
    module (PEP 615) rather than just checking the string isn't empty — a
    typo'd zone name is exactly the kind of mistake that should fail loudly
    at the moment it's constructed, not silently corrupt every downstream
    schedule/reminder calculation that reads it. `zoneinfo` needs the
    `tzdata` package to find this data on a platform with no system IANA
    database (Windows) — see `pyproject.toml`'s dependency comment.
    """

    value: str

    def __post_init__(self) -> None:
        ensure_not_empty(self.value, "timezone")
        try:
            ZoneInfo(self.value)
        except ZoneInfoNotFoundError as exc:
            raise DomainInvariantViolationError(
                f"timezone must be a valid IANA time zone name, got {self.value!r}"
            ) from exc


@dataclass(frozen=True)
class AuthMethod(ValueObject):
    """Which credential the user authenticates with, e.g.
    `AuthMethod("webauthn_passkey")` — the method named in the Architecture
    document (Section 15/21: "WebAuthn passkey (already in v1)"). One of
    `User`'s key attributes (Bible Section 4.1, Table 4).

    Deliberately a validated string, not a closed `Enum` like
    `AccountStatus`: which identity providers exist is an infrastructure/
    security concern (`app/infra`, a future auth adapter), not a business
    rule the domain layer should hard-code a fixed list of. The one
    invariant the domain does own is "it must actually name something", so
    that much is enforced here.
    """

    value: str

    def __post_init__(self) -> None:
        ensure_not_empty(self.value, "auth_method")


@dataclass(frozen=True, kw_only=True)
class UserProfile(ValueObject):
    """The physical-identity fields of the Bible's `Profile` aggregate
    (Section 4.2, Table 5) that this increment models as a value object
    nested in `User` rather than a standalone aggregate — see
    `docs/adr/0005-user-aggregate-first-increment.md`.

    `injury_flags` and `dietary_pattern` (also key attributes of `Profile`
    in the Bible) are references to the `SafetyFlag` and `NutritionPattern`
    aggregates respectively — neither exists yet, so they are omitted here
    rather than represented with a placeholder. They arrive on `UserProfile`
    (or its aggregate successor) alongside the Recovery & Safety and
    Nutrition bounded contexts.

    A `UserProfile` instance is valid the moment it exists — there is no
    partially-filled state — which is what lets `User.has_complete_profile`
    (`user.py`) be exactly "is `profile` not `None`", mapping the Bible's
    Profile lifecycle's Draft/Complete distinction onto `UserProfile |
    None` without a separate state machine. ("Stale" — a fact that hasn't
    been reconfirmed in N months — isn't modeled yet; it needs a `Clock`-
    driven staleness check this increment doesn't build.)
    """

    height_cm: float
    birth_year: int
    experience_level: ExperienceLevel
    sex: BiologicalSex | None = None

    def __post_init__(self) -> None:
        ensure_positive(self.height_cm, "height_cm")
        ensure(
            self.height_cm <= _MAX_PLAUSIBLE_HEIGHT_CM,
            f"height_cm must be a plausible human height (<= {_MAX_PLAUSIBLE_HEIGHT_CM}), "
            f"got {self.height_cm}",
        )
        ensure(
            _MIN_PLAUSIBLE_BIRTH_YEAR <= self.birth_year <= _MAX_PLAUSIBLE_BIRTH_YEAR,
            f"birth_year must be between {_MIN_PLAUSIBLE_BIRTH_YEAR} and "
            f"{_MAX_PLAUSIBLE_BIRTH_YEAR}, got {self.birth_year}",
        )


@dataclass(frozen=True, kw_only=True)
class QuietHours(ValueObject):
    """A notification blackout window (Product Bible: "Quiet hours /
    do-not-disturb windows", Notification & Automation, MVP tier).

    `starts_at`/`ends_at` are wall-clock times, not datetimes — a quiet
    window is "10pm to 7am every day", evaluated against the user's own
    `Timezone`, not a fixed instant. A window that wraps past midnight
    (`starts_at > ends_at`) is valid and expected (the common case, in
    fact); the only thing this rejects is a window of zero length.
    """

    starts_at: time
    ends_at: time

    def __post_init__(self) -> None:
        ensure(
            self.starts_at != self.ends_at,
            "quiet hours starts_at and ends_at must differ",
        )


@dataclass(frozen=True, kw_only=True)
class UserPreferences(ValueObject):
    """User-level settings scoped strictly to what the Product Bible
    documents at MVP tier and that plausibly belongs to the account itself
    rather than a specific device or a not-yet-built aggregate:

    - `quiet_hours`: Notification & Automation, MVP ("Quiet hours /
      do-not-disturb windows").
    - `biometric_app_lock_enabled`: Identity & Consent, MVP ("Local
      biometric app-lock"). Enforcement is a device-level concern (see the
      Bible's `DeviceSession` entity), but *whether the user wants it on*
      is naturally an account-level preference.
    - `available_equipment`: the equipment the user owns or regularly has
      access to, e.g. a home gym's fixed set — distinct from the Bible's
      `EnvironmentContext` (Section 4.3, Table 6), which is a per-session
      "where am I training right now" snapshot (see `context.py`'s module
      docstring for the same naming distinction on `UserContext`).
      `EnvironmentContext` doesn't exist yet as a build aggregate, and even
      once it does, a session-scoped "what's in this specific gym" is a
      different fact from an account-level "what do I own" default this
      field represents. Reuses `app.domain.exercise.value_objects.
      EquipmentRequirement` rather than defining a second equipment type —
      the same value already used by `Exercise.equipment_requirements` and
      by `ExerciseRecommendationRuleContext.available_equipment`
      (`docs/adr/0021-exercise-recommendation-composes-rule-outputs.md`,
      decision 4) to describe "one piece of equipment."

    "Communication style preference" (Identity & Consent, V2 tier) is
    deliberately not included yet — adding an unused field for a V2 feature
    would be exactly the kind of speculative addition the Engineering
    Master Plan's "boring technology" principle argues against. Add it when
    V2 scoping actually starts.

    All fields default so `UserPreferences()` — a new user who hasn't
    touched any setting yet — is always a valid value.
    """

    quiet_hours: QuietHours | None = None
    biometric_app_lock_enabled: bool = False
    available_equipment: frozenset[EquipmentRequirement] = frozenset()
