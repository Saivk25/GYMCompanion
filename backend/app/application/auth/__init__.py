"""The Authentication & Authorization Application Use Cases.

Coordinates `app.domain.auth.Credential` (and, for `Register` only,
`app.domain.user.User` too — see `handlers/register_handler.py`) with
repository interfaces, a `UnitOfWork`, and the two security-critical
collaborators this package is the *only* one allowed to touch:
`app.domain.auth.ports.PasswordHasher` and `...TokenService` — "No
password handling outside Authentication services" (this phase's own
rule) means exactly this package, nowhere else.

Same four-subpackage shape as every other Application Layer module
(`commands/`, `queries/`, `dto/`, `handlers/`) — see
`app.application.user`'s own package docstring for the general
reasoning, which applies here unchanged. See
`docs/adr/0032-authentication-and-authorization.md`.
"""
