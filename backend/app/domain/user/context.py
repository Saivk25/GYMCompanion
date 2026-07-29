"""`UserContext`: a read-only snapshot of a User for domain services.

Naming note, important enough to read before using this class: the Domain
Model & Decision Engine Bible also defines an aggregate literally called
"EnvironmentContext" — described in the product as "Context" (Section 4.3,
Table 6) — bundling a location, equipment set, and food-environment tag.
`UserContext` here is a *different, unrelated* concept and will remain one:
it carries no location/equipment/food data and will never be persisted or
given its own lifecycle. It exists so a future domain service (one of the
nine rule engines, none built yet) can be handed everything it needs to
know about a user in one immutable value, without either depending on the
mutable `User` aggregate directly or being handed a live `Repository` to
query mid-calculation. If this naming collision ever causes real confusion
once rule engines exist, renaming this class is a one-file change; it does
not rename the Bible's own "Context" concept.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.domain.shared_kernel.value_object import ValueObject
from app.domain.user.enums import AccountStatus
from app.domain.user.identifiers import UserId
from app.domain.user.value_objects import Locale, Timezone, UserPreferences, UserProfile

if TYPE_CHECKING:
    # Import only for the type checker: User -> nothing, UserContext ->
    # User (via from_user's parameter) would otherwise be a real circular
    # import at module load time, since user.py has no need to import this
    # module back.
    from app.domain.user.user import User


@dataclass(frozen=True, kw_only=True)
class UserContext(ValueObject):
    """An immutable snapshot of one User, taken at a point in time. See the
    module docstring for why this is not the Bible's `EnvironmentContext`.
    """

    user_id: UserId
    account_status: AccountStatus
    locale: Locale
    timezone: Timezone
    profile: UserProfile | None
    preferences: UserPreferences

    @classmethod
    def from_user(cls, user: User) -> UserContext:
        """Builds a snapshot from a live `User` aggregate. One-directional
        on purpose: `User` does not know this type exists, so an aggregate
        can never accidentally depend on a snapshot of itself.
        """
        return cls(
            user_id=user.id,
            account_status=user.account_status,
            locale=user.locale,
            timezone=user.timezone,
            profile=user.profile,
            preferences=user.preferences,
        )
