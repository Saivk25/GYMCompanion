"""The User aggregate's typed identifier.

A thin subclass of the shared kernel's `EntityId` — see
`app.domain.shared_kernel.identifiers` for why this is a subclass and not a
bare `uuid.UUID`. `UserId` itself carries no additional behavior; the
subclass exists purely so mypy treats a `UserId` and, say, a future
`WorkoutId` as distinct, non-interchangeable types.
"""

from __future__ import annotations

from app.domain.shared_kernel.identifiers import EntityId


class UserId(EntityId):
    """Strongly-typed identifier for the User aggregate root."""
