"""`UpdateNotesCommand`: the input to `UpdateNotesHandler`.

A separate command from `UpdateSleepCommand`/
`UpdateRecoveryMetricsCommand`, matching `Readiness.update_notes()`
being its own aggregate method with its own event
(`RecoveryNotesUpdated`) — the same "one command per named aggregate
method" shape `UpdateNotesCommand`
(`app.application.progress.commands.update_notes`) establishes for
`Progress.update_notes()`, and `UpdateNutritionNotesCommand`
(`app.application.nutrition.commands.update_notes`) establishes for
`Nutrition.update_notes()`. `notes` is required, not optional:
`Readiness.update_notes(notes: RecoveryNotes, ...)` takes no optional/
"leave unchanged" form, so neither does this command. Unlike
Nutrition's Phase 4, this command ships in the same phase as the rest
of this package rather than being added afterward — Phase 4's gap
(caught by the post-Phase-5 consistency review, see `docs/adr/0025-
nutrition-application-use-cases.md`'s addendum) is the reason every
aggregate's `update_notes()` now gets exposed from the start of its own
phase.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.value_objects import RecoveryNotes


@dataclass(frozen=True, kw_only=True)
class UpdateNotesCommand(Command):
    """Replace an existing Readiness check-in's notes wholesale."""

    readiness_id: ReadinessId
    notes: RecoveryNotes
