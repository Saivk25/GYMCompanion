"""`UpdateSleepCommand`: the input to `UpdateSleepHandler`.

**`None` means "leave unchanged," the same convention
`Readiness.update_sleep()` itself already documents** — `sleep_duration`/
`sleep_quality` are each independently optional, matching the aggregate
method's own signature exactly. A command's job is to carry a caller's
intent through to the aggregate method it invokes unmodified; this
command invents no meaning of its own for `None` beyond what
`Readiness.update_sleep()` already defines.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.shared.command import Command
from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.value_objects import SleepDuration, SleepQuality
from app.domain.user.identifiers import UserId


@dataclass(frozen=True, kw_only=True)
class UpdateSleepCommand(Command):
    """Replace whichever sleep fields are given on an existing Readiness
    check-in; a field left `None` keeps its current stored value.

    `requester_id` is the authenticated caller — see
    `app.application.readiness.queries.get_readiness.GetReadinessQuery`'s
    own module docstring for the full ownership-check reasoning, which
    applies identically here.
    """

    readiness_id: ReadinessId
    requester_id: UserId
    sleep_duration: SleepDuration | None = None
    sleep_quality: SleepQuality | None = None
