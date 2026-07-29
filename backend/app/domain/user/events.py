"""Domain events raised by the User aggregate.

Scoped deliberately to exactly the two events this increment needs —
`UserRegistered` (the terminal-ish fact of Bible workflow 6.1's onboarding
wizard entry point) and `UserProfileUpdated` (profile edits, read by
downstream Plan/Goal/Safety logic once those exist). The Bible's Section 9
event catalog names several more lifecycle events for this aggregate
(`UserOnboarded`, and by inference `UserSuspended`/`UserDeleted`/
`AccountPurged`-style events for the rest of the account-status state
machine in `user.py`) — those aren't raised yet because nothing in this
increment consumes them. Add each one when its first real subscriber
(Notification & Automation, AI Governance's purge cascade, ...) is actually
being built, not speculatively ahead of that. See each `DomainEvent`
subclass in `app.domain.shared_kernel.events` for why `kw_only=True` is
required here.
"""

from dataclasses import dataclass

from app.domain.shared_kernel.events import DomainEvent
from app.domain.user.identifiers import UserId
from app.domain.user.value_objects import Locale, Timezone, UserProfile


@dataclass(frozen=True, kw_only=True)
class UserRegistered(DomainEvent):
    """A new User was created via `User.register(...)`. `locale` and
    `timezone` are carried on the event (rather than requiring a listener
    to re-fetch the aggregate) since they're exactly what a first-run
    notification/localization concern would need immediately.
    """

    user_id: UserId
    locale: Locale
    timezone: Timezone


@dataclass(frozen=True, kw_only=True)
class UserProfileUpdated(DomainEvent):
    """`User.update_profile(...)` replaced the user's `UserProfile`. Carries
    the full new profile rather than a diff — the aggregate has no previous-
    value tracking to compute one from, and every documented downstream
    reader (Plan generation, Safety Rule evaluation) needs the current
    profile in full, not a delta.
    """

    user_id: UserId
    profile: UserProfile
