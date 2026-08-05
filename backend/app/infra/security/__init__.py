"""Concrete, library-backed implementations of the two ports
`app.domain.auth.ports` declares — `PasswordHasher` (bcrypt) and
`TokenService` (PyJWT) — wired in at the composition root
(`app.composition.container.Container`), never constructed directly by
application or API code. See that module's own docstring for why
these algorithms live only here, never in `app.domain`.
"""
