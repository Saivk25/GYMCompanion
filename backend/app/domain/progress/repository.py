"""The persistence contract for the Progress aggregate.

Adds nothing beyond the shared kernel's `Repository[TAggregate, TId]`
(`get`/`add`/`remove`), matching every other aggregate's repository in this
codebase: no query method here (e.g. "find every Progress record for a
User in a date range" — the obvious candidate for a history view) is
grounded in a concrete caller in this codebase yet. `app/infra/` provides
the real, Postgres-backed implementation.

Deliberately still just `get`/`add`/`remove`, with no `update` — see
`progress.py`'s class docstring and
`docs/adr/0010-progress-immutability-is-a-policy-not-a-guard.md` for why
that omission does not, by itself, enforce this aggregate's immutability
rule (every other aggregate's repository is shaped identically and none of
them are meant to be immutable).
"""

from app.domain.progress.identifiers import ProgressId
from app.domain.progress.progress import Progress
from app.domain.shared_kernel.repository import Repository


class ProgressRepository(Repository[Progress, ProgressId]):
    """Persistence contract for the Progress aggregate. See the module
    docstring for why it declares no methods beyond the shared kernel's.
    """
