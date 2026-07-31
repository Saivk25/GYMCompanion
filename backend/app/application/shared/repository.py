"""Re-exports the Domain Layer's own generic repository abstraction for
use inside `app.application`.

**Deliberately not a new interface.** `app.domain.shared_kernel.
repository.Repository[TAggregate, TId]` (Sprint 1) is already the
framework-independent persistence contract every aggregate's own
repository interface (`UserRepository`, `ExerciseRepository`, ...)
extends — `get()`/`add()`/`remove()`, no SQLAlchemy or storage
knowledge anywhere in its definition. Defining a second, structurally
identical `Repository` here would be exactly the duplication this
phase's own task explicitly forbids for exceptions, applied to a second
concept the same reasoning covers just as well: the Domain Layer
already owns this contract, and "generic repository abstractions only"
is satisfied by depending on the one that already exists, not by
inventing a parallel one. See
`docs/adr/0022-application-layer-foundation.md`.

Re-exported under this layer's own import path — `from
app.application.shared.repository import Repository` — purely so code
inside `app.application` has one consistent place to import its own
dependencies from, without reaching into `app.domain.shared_kernel`
directly at every call site. The type itself, and everything it
guarantees, is unchanged.
"""

from app.domain.shared_kernel.repository import Repository as Repository

__all__ = ["Repository"]
