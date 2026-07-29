"""Closed-set categorical values used by the User aggregate.

Each of these is a genuinely closed, business-meaningful set documented in
the Domain Model & Decision Engine Bible (Section 4.1, Table 4 for
`AccountStatus`; Section 4.2, Table 5 for `ExperienceLevel`/`BiologicalSex`),
not a speculative classification invented for this implementation. Plain
`enum.Enum` (stdlib) rather than a value object: there is no invariant to
enforce beyond "one of these exact members", which `Enum` already gives for
free at zero cost.

Each inherits `str` as well as `Enum` so a member serializes to exactly its
`.value` wherever it's written to JSON, a database column, or an event
payload — matching `app/infra/models.py`'s `_ACCOUNT_STATUSES` column
values verbatim for `AccountStatus`.
"""

from enum import Enum


class AccountStatus(str, Enum):
    """The User aggregate's lifecycle (Bible Section 4.1, Table 4,
    "Lifecycle / states"): Invited -> Active -> Suspended (optional) ->
    Deleted (soft) -> Purged (hard). The legal transitions between these —
    including the one documented exception, Suspended -> Active — are
    enforced by `User`'s own transition table (`user.py`), not by this
    enum; this type only names the possible values.
    """

    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"
    PURGED = "purged"


class ExperienceLevel(str, Enum):
    """Training-experience tier, one of `UserProfile`'s key attributes
    (Bible Section 4.2, Table 5). Read by Plan generation and Safety Rule
    evaluation (not yet implemented) to scale intensity/volume defaults.
    """

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class BiologicalSex(str, Enum):
    """The value behind `UserProfile.sex` when the user chooses to disclose
    it — the Bible names this field `sex_optional` (Section 4.2, Table 5)
    specifically because disclosure is optional; that optionality is
    represented by `UserProfile.sex` being `BiologicalSex | None`, not by a
    member on this enum. Only the two values a BMR formula (e.g.
    Mifflin-St Jeor) actually branches on are named here; a user who
    declines to answer simply leaves the field `None` rather than picking a
    third member that would still have to fall back to some default
    formula internally.
    """

    FEMALE = "female"
    MALE = "male"
