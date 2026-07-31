"""`UserDTO`: the read-only projection of a `User` aggregate returned to
whatever calls a User query handler.

**Not the same type as `app.domain.user.context.UserContext`,
deliberately.** `UserContext` is explicitly scoped, by its own module
docstring, to "a future domain service" (a rule engine) — it is a
domain-internal snapshot, one-directional (`User` does not know it
exists), and never crosses the Application Layer boundary. `UserDTO`
answers a different question: "what does a caller of `GetUserQuery`
receive back" — a future API layer's response shape, not a rule
engine's input. The two types happen to overlap in most of their
fields today because both are, at bottom, "a read-only view of a
User's state," but they exist for different consumers with different
reasons to change independently (a future API-versioning concern for
`UserDTO`; a future rule-engine-input concern for `UserContext`) —
collapsing them onto one type would couple those two reasons together
for no benefit. See `docs/adr/0023-user-application-use-cases.md`.

A `UserDTO` carries plain domain value objects (`Locale`, `Timezone`,
...) rather than primitives — this phase builds no serialization
boundary (no FastAPI, no Pydantic model) that would need primitives,
and converting to those types here would be premature: the first real
consumer (a future API layer) is exactly where that conversion
decision belongs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from app.domain.user.enums import AccountStatus
from app.domain.user.identifiers import UserId
from app.domain.user.value_objects import AuthMethod, Locale, Timezone, UserPreferences, UserProfile

if TYPE_CHECKING:
    # Import only for the type checker — see `app.domain.user.context`'s
    # identical use of TYPE_CHECKING for why this avoids a real circular
    # import at module load time (User has no need to import this module
    # back).
    from app.domain.user.user import User


@dataclass(frozen=True, kw_only=True)
class UserDTO:
    """An immutable, read-only snapshot of one `User`, taken at query
    time. See the module docstring for why this is not `UserContext`.
    """

    user_id: UserId
    account_status: AccountStatus
    created_at: datetime
    locale: Locale
    timezone: Timezone
    auth_method: AuthMethod
    profile: UserProfile | None
    preferences: UserPreferences
    has_complete_profile: bool

    @classmethod
    def from_user(cls, user: User) -> UserDTO:
        """Builds a DTO from a live `User` aggregate. One-directional on
        purpose, mirroring `UserContext.from_user` — `User` never
        depends on this type.
        """
        return cls(
            user_id=user.id,
            account_status=user.account_status,
            created_at=user.created_at,
            locale=user.locale,
            timezone=user.timezone,
            auth_method=user.auth_method,
            profile=user.profile,
            preferences=user.preferences,
            has_complete_profile=user.has_complete_profile,
        )
