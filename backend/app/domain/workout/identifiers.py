"""The Workout aggregate's typed identifier.

Same pattern as `app.domain.user.identifiers.UserId` — a thin subclass of
the shared kernel's `EntityId` so mypy treats a `WorkoutId` and a `UserId`
(or any future aggregate's id) as distinct, non-interchangeable types, at
zero runtime cost.
"""

from __future__ import annotations

from app.domain.shared_kernel.identifiers import EntityId


class WorkoutId(EntityId):
    """Strongly-typed identifier for the Workout aggregate root."""
