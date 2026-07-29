"""Marker base for domain services: stateless business logic that doesn't
belong to any single entity or value object — most notably the nine rule
engines the Domain Model & Decision Engine Bible specifies (Section 10),
each of which operates across data rather than living as a method on one
aggregate.

Deliberately not prescribing a shared method signature (an `evaluate()`
or `execute()` every subclass must implement): the nine rule engines take
different inputs and return different outputs, and forcing a common
signature onto genuinely different shapes is exactly the kind of
speculative structure this project's engineering principles argue against.
`DomainService` exists as a shared marker/base purely so domain services
are identifiable as a category (for import-boundary tests, documentation,
and future cross-cutting concerns like logging or timing decorators),
not to force a common interface prematurely.

A domain service must still obey every domain-layer rule: no
`app.infra`/`app.api`/`app.ai` imports, constructed from other domain
types only, any time it needs come from an injected `Clock`
(`clock.py`), never from calling `datetime.now()` itself.

Plain class, not `ABC`: with no abstract method to declare, inheriting
from `ABC` here would only give the misleading appearance of enforcement
(an `ABC` with no `@abstractmethod` is instantiable directly, same as any
other class) without actually preventing anything.
"""


class DomainService:
    """Marker base for stateless domain services. See the module
    docstring for why no abstract method is declared here."""
