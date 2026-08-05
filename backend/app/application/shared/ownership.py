"""`ensure_owner()`: the single place every handler's "does the caller
own this resource" comparison happens.

Resource ownership authorization is an Application Layer responsibility,
not an API Layer or Domain Layer one — a handler already loads the
aggregate it needs (to mutate it or to build a DTO from it), so it is
the natural place to compare that aggregate's own `user_id` against the
authenticated caller's id before doing anything else with it. Putting
this check in the API layer would mean a route loading the resource
itself just to authorize it, then discarding that load and asking the
handler to load it again — the "No repository access from routes" rule
this codebase's routes already follow rules that out (see
`docs/TECH_DEBT.md`'s TD-0002, the gap this module closes). Putting it
in the Domain Layer would mean an aggregate comparing itself against a
caller identity it has no business knowing about — an aggregate enforces
its own invariants, never who is allowed to ask about them.

Extracted as a single, small, pure helper *from the start of this phase*
— unlike `advisory_warnings()` (`app.application.shared.
advisory_warnings`), which existed as 11 duplicated private copies for
four phases before TD-0001 finally triggered its extraction. Same
duplication shape (one owner/requester comparison, ~27 call sites across
six aggregates), same "small pure function called from many handlers"
role, but learning directly from that history: this phase's own
directive is explicit that authorization logic must not be duplicated,
so the extraction happens now rather than being deferred to a future
TD item. See `docs/adr/0033-resource-ownership-authorization.md`.

Returns a plain `str | None` — a denial message, or `None` when the
requester is the owner — rather than a full `ApplicationResult[T]`.
`ApplicationResult` is `Generic[T]`, and this function has no `T` of its
own to bind (it never touches a handler's return value); a caller
constructs `ApplicationResult.forbid([...])` directly at its own
`return` statement, where `T` is inferred from the handler's own return
type annotation, the same way every handler already writes
`ApplicationResult.fail([...])` inline rather than through a
result-returning wrapper.
"""

from __future__ import annotations

from app.domain.user.identifiers import UserId

_OWNERSHIP_DENIED_MESSAGE = "you do not have permission to access this resource"


def ensure_owner(*, owner_id: UserId, requester_id: UserId) -> str | None:
    """Compares `owner_id` (the resource's own `user_id`) against
    `requester_id` (the authenticated caller, threaded into the Command/
    Query as `requester_id` by every route in `app.api.routes.v1`).
    Returns a denial message when they differ, `None` when they match.
    """
    if owner_id != requester_id:
        return _OWNERSHIP_DENIED_MESSAGE
    return None
