"""`Role` and `Permission`: the authorization model.

Deliberately future-proof rather than a single hard-coded boolean
("is_admin"): a closed `Enum` for each concept plus a `ROLE_PERMISSIONS`
mapping table between them is exactly enough structure that adding a
second role (e.g. `COACH`) or a second permission later is a data change
— one new enum member, one new mapping entry — not a redesign. Only one
role is active today (`MEMBER`), matching this phase's own instruction
("future-proof, even if only one role is active"); no second role is
added speculatively.
"""

from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    """Every role a `Credential` can hold. `MEMBER` is the only role
    granted today — every registered user gets it, there is no
    elevation path yet."""

    MEMBER = "member"


class Permission(str, Enum):
    """Every permission this codebase's authorization model currently
    distinguishes. `MANAGE_OWN_DATA` is deliberately the only one: this
    phase secures *authentication* (proving who you are) and the single
    coarse-grained authorization fact every endpoint needs today ("is
    there an authenticated identity at all"), not a fine-grained,
    per-aggregate permission system nothing in this codebase yet
    requires — see `docs/adr/0032-authentication-and-authorization.md`.
    """

    MANAGE_OWN_DATA = "manage_own_data"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.MEMBER: frozenset({Permission.MANAGE_OWN_DATA}),
}
