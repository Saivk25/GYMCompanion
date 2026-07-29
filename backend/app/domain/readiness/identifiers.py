"""The Readiness aggregate's typed identifier.

Same pattern as every other aggregate's identifier in this codebase — a
thin subclass of the shared kernel's `EntityId` so mypy treats a
`ReadinessId` as distinct from every other aggregate's id, at zero runtime
cost.
"""

from __future__ import annotations

from app.domain.shared_kernel.identifiers import EntityId


class ReadinessId(EntityId):
    """Strongly-typed identifier for the Readiness aggregate root."""
