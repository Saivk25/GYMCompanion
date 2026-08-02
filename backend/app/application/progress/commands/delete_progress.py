"""`DeleteProgressCommand`: the input to `DeleteProgressHandler`.

`Progress` has no delete/soft-delete method of its own and raises no
`ProgressDeleted` event — `events.py` is scoped to exactly the four
events `record()`/`update_body_composition()`/`update_measurements()`/
`update_notes()` actually raise, the same "raise only what the
aggregate's own methods actually do" discipline every other aggregate's
`events.py` follows. `DeleteProgressHandler` therefore calls
`ProgressRepository.remove()` directly rather than an aggregate method —
see that handler's own module docstring, and the identical reasoning
`DeleteNutritionCommand` (`app.application.nutrition.commands.
delete_nutrition`) documents for `Nutrition`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.progress.identifiers import ProgressId


@dataclass(frozen=True, kw_only=True)
class DeleteProgressCommand(Command):
    """Permanently remove an existing Progress record."""

    progress_id: ProgressId
