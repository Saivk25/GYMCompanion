# ADR 0032: Authentication & Authorization — a separate `Credential` aggregate, password + JWT (not passkeys), Bearer tokens, no RLS on `credentials`, and authenticated identity replacing client-supplied `user_id`

- Status: accepted
- Date: 2026-08-05

## Context

The API Layer (`docs/adr/0031`) exposed 37 endpoints across five modules
with explicit, disclosed "no authentication" scope — every route trusted
a caller-supplied `user_id` with no verification the caller actually
*was* that user, and ADR 0031's own Consequences section named this the
one thing that must close before the API is exposed to any untrusted
network. This phase's brief is exactly that: secure the existing API,
integrating with the existing architecture, without bypassing the
Application Layer.

The Engineering Master Plan's security section names "passkey auth
(WebAuthn)" as the intended v1 authentication mechanism. This phase's
own directive instead explicitly specifies password hashing, JWT access
tokens, and JWT refresh tokens — a deliberate, scoped divergence from
that document, not an oversight (see decision 2).

This phase builds: a new `Credential` aggregate and its supporting value
objects/enums/ports (Domain), five Commands/Queries/Handlers/DTOs
(Application), `BcryptPasswordHasher`/`JwtTokenService`/a `credentials`
table with no RLS (Infrastructure), and five new routes plus a
`get_current_user_id` dependency now required by every one of the 37
pre-existing routes (API) — the first phase to touch every layer at
once, and the first to modify already-accepted API Layer route modules
rather than only adding new ones.

## Decision

1. **`Credential` (`app.domain.auth.credential`) is a new aggregate,
   separate from `User`, sharing `User`'s `UserId` as its own identity
   (strict 1:1, no new identifier type).** Extending `User` directly
   with `email`/`password_hash` fields was rejected: `User` (ADR 0005)
   is an already-accepted, already-tested aggregate whose own scope is
   profile/preferences, and "No password handling outside Authentication
   services" (this phase's own rule) reads more naturally as a bounded-
   context separation — a whole aggregate `app.application.auth` alone
   is permitted to touch — than as a field-level convention every other
   `User`-touching handler would need to remember to respect. `Credential.
   register()` and `User.register()` are both called by `RegisterHandler`
   in one `UnitOfWork`, sharing one freshly generated `UserId` — the only
   handler in this codebase orchestrating two aggregates, because `POST
   /register` is the one operation where a `Credential` with no matching
   `User` (or vice versa) is never a valid state.

2. **Password hashing + JWT, not the Master Plan's "passkey (WebAuthn)"
   — a deliberate, disclosed divergence, not silent drift.** This
   phase's own directive is explicit and enumerates "Password hashing,
   JWT access tokens, JWT refresh tokens" under Security; WebAuthn
   ceremonies require client-side ("navigator.credentials") support this
   phase has no Flutter client to provide, and building it here would be
   scope creep past "Do NOT begin Flutter." `app.domain.user.value_objects.
   AuthMethod` — a bare string, not a closed enum, per its own existing
   docstring — already names "WebAuthn passkey" only as an *example*
   value, precisely to accommodate `AuthMethod("password")` (what
   `RegisterHandler` actually stamps) without needing to change that
   type. A future phase can add real WebAuthn ceremonies as a second,
   additional `AuthMethod` value and a second `Credential`-adjacent
   verification path — `Credential`'s own `password_hash: PasswordHash`
   field would need to become optional at that point, a forward-
   compatible, non-breaking change, not a redesign.

3. **Bearer tokens (`Authorization: Bearer <token>`), not cookies.** The
   Master Plan's System Architecture names Flutter (a native mobile app)
   as the primary client — a Bearer token in a header is the standard,
   framework-agnostic mechanism a mobile HTTP client attaches to every
   request; secure cookies bring CSRF-defense and cookie-jar concerns
   that only make sense for a browser-hosted client, which this
   application is not primarily building for. `app.api.deps.
   get_current_user_id` declares `fastapi.security.HTTPBearer` as its
   dependency specifically because doing so is also what makes FastAPI
   emit a `securitySchemes: {bearerAuth: {type: http, scheme: bearer}}`
   block in the generated OpenAPI document — satisfying this phase's own
   "OpenAPI security definitions" verification item as a byproduct of the
   dependency declaration itself, with no hand-written schema needed.

4. **Token revocation is a `token_version: int` counter on `Credential`,
   embedded only in refresh-token claims — no Redis, no blocklist
   table.** `Credential.revoke_tokens()` (called by `LogoutHandler`)
   bumps `token_version` and records a `TokensRevoked` domain event;
   `RefreshHandler` rejects any refresh token whose embedded
   `token_version` no longer matches the `Credential`'s current one,
   covering both "this token was revoked by an explicit logout" and "the
   credential no longer exists" with the same generic rejection (a
   caller cannot distinguish, and does not need to — both mean "log in
   again"). Access tokens intentionally do **not** carry or check
   `token_version` — they carry only `user_id` and `role`, and remain
   valid for their full (short, `access_token_ttl_minutes: int = 15`)
   lifetime even after a logout. This is a disclosed trade-off, not an
   oversight: closing it would require a real revocation store (Redis or
   a database blocklist) the Master Plan mentions but this phase's stack
   does not yet include — deferred, not implemented, and named again in
   Consequences.

5. **No RLS on the `credentials` table — a second, structurally
   different exception from the "every user-owned table gets RLS"
   pattern ADR 0029 established (`exercises` being the first, for an
   unrelated reason: it carries no `user_id` at all).** Every other
   RLS policy in this codebase is shaped `USING (user_id::text =
   current_setting('app.current_user_id', true))` — it presupposes the
   caller's tenant identity is already known before the query runs.
   `POST /login`'s defining property is the opposite: it looks up a
   `Credential` **by email**, before any tenant identity exists to set
   that session variable to. An RLS policy in that shape is
   structurally unsatisfiable for the one query that establishes
   identity in the first place. `CredentialSqlRepository` therefore
   never calls `tenant_scope()`, and the `credentials` table's migration
   creates no RLS policy — documented at length in both
   `app/infra/models/credential.py` and the migration itself, explicitly
   distinguishing this reason from `exercises`'s.

6. **`Container.handler()` (`app/composition/container.py`) was
   generalized from three hardcoded `if "dispatcher"/"clock" in
   parameters` branches to a name-keyed dict loop over every shared
   singleton `Container` holds.** ADR 0030 (decision 4) already
   established that every handler's constructor follows one of a small,
   enumerable set of shapes, discovered by inspecting real signatures —
   this phase's five new handlers need two collaborators
   (`password_hasher`, `token_service`) no handler before them did,
   which would have been a fourth and fifth hardcoded `if` branch under
   the old shape. The generalized version — `available: dict[str,
   object]` mapping parameter name to collaborator, `for name, value in
   available.items(): if name in parameters: kwargs[name] = value` —
   scales to a sixth collaborator with a one-line addition to the dict,
   not a new branch, and is exercised identically by the existing
   `tests/composition/test_dependency_graph.py` parametrization (updated
   from 44 to 49 handlers) with no test-shape change needed.

7. **`app.api.deps.get_current_user_id` returns a bare `UserId`, not the
   full `AccessTokenClaims` or a `CurrentUserDTO`.** Every protected
   route in this codebase needs exactly one thing from the caller's
   identity — "who is calling" — to either build a Command/Query or (for
   the four-route class described in decision 9) simply require *a*
   authenticated caller at all; a route wanting the full profile already
   has `GET /me` (`GetCurrentUserHandler`) to ask for it explicitly. This
   also keeps every `v1` route module free of any reason to import
   `app.domain.auth` at all — confirmed by `tests/api/
   test_import_boundaries.py` continuing to pass with `app.domain.auth`
   appearing only in `app/api/deps.py` and `app/api/routes/auth.py`
   across the whole `app/api` package.

8. **A fourth `unwrap_or_*` helper, `unwrap_or_401`, was added to
   `app/api/errors.py` for `LoginHandler`/`RefreshHandler` failures.**
   ADR 0031's decision 4 established that `ApplicationResult` carries no
   structured error code, so status mapping is keyed by *which kind of
   handler produced the failure* — a wrong password or a revoked/expired
   refresh token is neither "not found" (`unwrap_or_404`; these routes
   address no resource by id) nor an ordinary caller-correctable 400
   (`unwrap_or_400`; the request was shaped correctly, the *credential*
   was rejected) nor an unexpected 500 (`unwrap_or_500`; this is an
   expected, routine outcome). HTTP 401 Unauthorized is what the other
   three categories do not already name. `RegisterHandler` still uses
   `unwrap_or_400` — "email already registered" is an ordinary
   caller-correctable validation failure, matching every other command
   handler's failure shape.

9. **Every one of the 37 pre-existing `v1` routes now depends on
   `get_current_user_id`; the four create/list routes that took a
   client-supplied `user_id` now derive it from the authenticated caller
   instead.** `CreateGoalRequest`/`RecordNutritionRequest`/
   `RecordProgressRequest`/`RecordReadinessRequest`/`CreateWorkoutRequest`
   lost their `user_id: str` field; each schema's `to_command()` gained a
   `user_id: UserId` parameter the route supplies from
   `get_current_user_id`, not from request data — a caller can no longer
   create a resource, or list another user's resources, by naming an
   arbitrary `user_id`. The remaining 27 routes (every `GET`/`PATCH`/
   `PUT`/`DELETE`/action route addressing a specific resource id) depend
   on `get_current_user_id` only to require *a* valid authenticated
   caller — they bind the result to `_user_id` and do not yet check that
   the caller *owns* the resource named in the path. This is a
   deliberate, named scope boundary, not an oversight — see Consequences
   and the Architecture Delta Review's Technical Debt answer.

## Consequences

**Per-resource ownership authorization is not enforced.** Any
authenticated caller can `GET`/`PATCH`/`DELETE` any `goal_id`/
`workout_id`/`nutrition_id`/etc. that exists, regardless of who created
it — decision 9's 27 routes require *a* valid token, not *the right*
one. Closing this gap needs each `GetXHandler`/`UpdateXHandler`/
`DeleteXHandler` (or the route layer, if kept thin) to compare the
resource's own `user_id` against the caller's — a real, nontrivial
change to 27 already-accepted routes and arguably several handlers, out
of scope for a phase whose brief is "secure the existing API," not
"redesign resource ownership." Tracked as a named Technical Debt item
(see the Architecture Delta Review); the next phase that touches any of
these five modules should close it before, not alongside, unrelated
feature work.

**Access tokens remain valid until natural expiry after logout, even
though refresh tokens are immediately revoked (decision 4).** A stolen
access token is usable for up to `access_token_ttl_minutes` (15,
default) regardless of a legitimate logout — standard short-lived-
access-token behavior, not a bug, but real exposure a Redis-backed or
database-backed access-token blocklist would close. Not implemented:
absent from this phase's stack and directive.

**No rate limiting on `/login` or `/register`.** The Master Plan
mentions rate limiting; nothing in this codebase's current stack
provides it (no Redis, no middleware). A credential-stuffing or
registration-spam defense is future work, not silently assumed to exist.

**The full register -> login -> refresh -> logout flow, and a real
protected `v1` route, are proven end to end only against a real,
migrated Postgres database (`tests/api/test_auth_flow_integration.py`,
`@pytest.mark.integration`) — the same "skips without a reachable
Postgres" constraint every integration test in this codebase has carried
since ADR 0029.** These did not run against a live database in this
sandbox; they are expected to run in CI, where Postgres is reachable.
Routing/mapping correctness for all five new auth routes, and for every
modified `v1` route, is proven separately (and does run here) via the
existing `stub_client` strategy (ADR 0031, decision 9).

**`Role`/`Permission`/`ROLE_PERMISSIONS` (`app.domain.auth.enums`) are
structurally future-proof but not yet consumed by any authorization
check.** `Role.MEMBER` is the only role that exists; `Credential.
has_permission()` is implemented and unit-tested but no handler or route
calls it. This mirrors ADR 0030's own disclosed `RuleEngines`-unconsumed
pattern (decision 5 there) — the seam exists, proven constructible, and
is not exercised in production code paths yet. A future admin/coach role
is additive: a new `Role` member, new `ROLE_PERMISSIONS` entries, and
call sites for `has_permission()` this phase deliberately does not
invent speculatively.

**No ADR became obsolete.** ADR 0031's Consequences section explicitly
named "Authentication is entirely absent" as an open gap this phase was
always expected to close — this phase closes exactly that gap and
changes nothing else ADR 0031 decided (schema conventions, `unwrap_or_*`
mapping for the three pre-existing categories, versioning, health
endpoints). ADR 0029's no-RLS-on-`exercises` precedent is extended, not
contradicted, by decision 5's no-RLS-on-`credentials` — two tables, two
distinct and separately documented reasons, not a reversal of the
RLS-by-default policy itself (every other table in this codebase still
gets RLS).
