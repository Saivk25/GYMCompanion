"""`DeleteReadinessCommand`: the input to `DeleteReadinessHandler`.

`Readiness` has no soft-delete/status concept the way `User`/`Workout`
do (`readiness.py`'s module docstring: "No status enum and no
lifecycle... a check-in is a fact captured at a point in time"), and no
`ReadinessDeleted` event exists on the aggregate (`events.py` is scoped
to exactly the four events `record()`/`update_sleep()`/
`update_recovery_metrics()`/`update_notes()` raise). Deleting a logged
check-in outright — correcting a mis-logged entry — is therefore a
`ReadinessRepository.remove()` call, not an aggregate method invocation,
the same shape `DeleteNutritionCommand`/`DeleteProgressCommand` already
establish; see `DeleteReadinessHandler` for the consequence this has
for event dispatch.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.readiness.identifiers import ReadinessId


@dataclass(frozen=True, kw_only=True)
class DeleteReadinessCommand(Command):
    """Permanently remove an existing Readiness check-in."""

    readiness_id: ReadinessId
