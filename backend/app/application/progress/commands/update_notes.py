"""`UpdateNotesCommand`: the input to `UpdateNotesHandler`.

A separate command from `UpdateBodyCompositionCommand`/
`UpdateMeasurementsCommand`, matching `Progress.update_notes()` being
its own aggregate method with its own event (`ProgressNotesUpdated`) —
the same "one command per named aggregate method" shape
`UpdateWaterCommand` (`app.application.nutrition.commands.update_water`)
establishes for `Nutrition.update_water()`. `notes` is required, not
optional: `Progress.update_notes(notes: ProgressNotes, ...)` takes no
optional/"leave unchanged" form, so neither does this command.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.progress.identifiers import ProgressId
from app.domain.progress.value_objects import ProgressNotes


@dataclass(frozen=True, kw_only=True)
class UpdateNotesCommand(Command):
    """Replace an existing Progress record's notes wholesale."""

    progress_id: ProgressId
    notes: ProgressNotes
