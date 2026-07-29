"""The User aggregate: Sprint 2's first real aggregate, built on the Sprint 1
shared kernel (`app.domain.shared_kernel`). Identity & Consent bounded
context (Domain Model & Decision Engine Bible, Section 3, Table 2), root
aggregate deep dive in Section 4.1.

Scope of this first increment — deliberately smaller than the full Identity
& Consent bounded context, not an oversight:

- `Profile` (Bible Section 4.2) is a standalone aggregate in the Bible, with
  its own Draft -> Complete -> Stale -> Complete lifecycle and independent
  versioning against `AIInferenceRecord` snapshots. Building that in full
  now would be speculative — nothing yet consumes a Profile edit
  independently of its owning User. This increment models `UserProfile` as
  an immutable value object owned by `User` instead; see
  `docs/adr/0005-user-aggregate-first-increment.md` for the full reasoning
  and the migration path when a real second consumer justifies promoting it
  to its own aggregate.
- `Consent` and `DeviceSession` (also Identity & Consent, Table 2) are not
  modeled yet — nothing in this increment's scope needs them.
- The nine rule engines, every other bounded context's aggregates, and any
  AI/infra concern are explicitly out of scope here, per the Engineering
  Master Plan's "one aggregate at a time" sequencing.

Depends on nothing outside the Python standard library and
`app.domain.shared_kernel` — enforced by the same statically-checked rule
as the rest of `app/domain` (`tests/domain/test_import_boundaries.py`).
"""

from app.domain.user.context import UserContext
from app.domain.user.enums import AccountStatus, BiologicalSex, ExperienceLevel
from app.domain.user.events import UserProfileUpdated, UserRegistered
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

__all__ = [
    "AccountStatus",
    "AuthMethod",
    "BiologicalSex",
    "ExperienceLevel",
    "Locale",
    "QuietHours",
    "Timezone",
    "User",
    "UserContext",
    "UserId",
    "UserPreferences",
    "UserProfile",
    "UserProfileUpdated",
    "UserRegistered",
    "UserRepository",
]
