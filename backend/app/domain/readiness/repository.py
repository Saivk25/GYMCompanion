"""The persistence contract for the Readiness aggregate.

Adds nothing beyond the shared kernel's `Repository[TAggregate, TId]`
(`get`/`add`/`remove`), matching every other aggregate's repository in this
codebase: no query method here (e.g. "find the Readiness entry for a User
on a given date", the obvious candidate for enforcing the Bible's "one
check-in per day" rule — see `readiness.py`'s module docstring) is grounded
in a concrete caller in this codebase yet. `app/infra/` provides the real,
Postgres-backed implementation.
"""

from app.domain.readiness.identifiers import ReadinessId
from app.domain.readiness.readiness import Readiness
from app.domain.shared_kernel.repository import Repository


class ReadinessRepository(Repository[Readiness, ReadinessId]):
    """Persistence contract for the Readiness aggregate. See the module
    docstring for why it declares no methods beyond the shared kernel's.
    """
