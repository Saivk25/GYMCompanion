"""The Authentication & Authorization bounded context.

Owns the `Credential` aggregate — the login identity (email + password
hash) layered on top of an existing `User`, kept in its own package
rather than added to `app.domain.user` so the already-accepted, 100%-
covered `User` aggregate, its DTO, handlers, SQL model, and migration
stay completely untouched by this phase (see
`docs/adr/0032-authentication-and-authorization.md`, decision 1).

`Credential.id` is a `UserId` (`app.domain.user.identifiers`), not a new
identifier type: the relationship is strictly one-to-one and always will
be (one login identity per User), so inventing a second id type for the
same underlying entity would be exactly the kind of speculative
abstraction this codebase's own conventions (see
`app.domain.user.repository`'s "add a method only once a concrete caller
needs it") argue against.
"""
