"""The persistence contract for the User aggregate.

Adds nothing beyond the shared kernel's `Repository[TAggregate, TId]`
(`get`/`add`/`remove`) — no query method here is grounded in a documented
requirement yet (e.g. "look up a user by their auth identity" needs a real
identity-provider shape this increment doesn't model; see
`value_objects.py`'s `AuthMethod` docstring). Add a method here only once a
concrete caller needs it, not speculatively. `app/infra/` provides the real,
Postgres-backed implementation.
"""

from app.domain.shared_kernel.repository import Repository
from app.domain.user.identifiers import UserId
from app.domain.user.user import User


class UserRepository(Repository[User, UserId]):
    """Persistence contract for the User aggregate. See the module
    docstring for why it declares no methods beyond the shared kernel's.
    """
