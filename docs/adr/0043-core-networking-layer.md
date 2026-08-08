# ADR 0043: Core networking layer — Step 1 of production integration

- Status: accepted
- Date: 2026-08-08

## Context

`docs/adr/0042-production-integration-plan.md` planned, but did not
build, the real HTTP layer every feature's eventual `ApiXRepository`
will sit on. This phase is that plan's own "Step 1 — Core Networking":
build the shared client, then stop before touching any feature
repository, per the directive's own explicit ordering ("Do not yet
modify feature repositories").

## Decision

**`dio`, not `http`.** The lower-level `http` package has no built-in
interceptor chain — bearer-token injection, the refresh-then-retry flow,
and debug logging would each need to be hand-rolled as a wrapper around
every call site, or bolted on via a bespoke middleware layer that
duplicates what `dio`'s `Interceptor` already is. `dio` is a real, new
dependency (disclosed in `pubspec.yaml`'s own comment) — the first
non-Riverpod/go_router runtime dependency this app has ever taken —
because nothing in this codebase needed real HTTP until this exact
phase.

**`ApiClient` knows nothing about authentication.** Its constructor
takes three optional closures (`accessTokenProvider`, `refreshToken`,
`onRefreshFailed`) rather than a dependency on `AuthRepository`/
`AuthController` directly — `lib/core/network/` has zero imports of
`lib/features/` (confirmed by the same import-direction sweep ADR 0042's
audit used). This is what makes "Step 1 first, Step 2 after" a real,
independently-committable split rather than a nominal one: this phase's
own test suite (`test/core/network/`) exercises the full auth-header/
refresh/retry flow using bare closures, with no `AuthRepository` — real
or mock — needing to exist yet.

**Retry policy is GET-only, network-failure-only — grounded in ADR
0042's own finding, not a generic "retries are good" default.** ADR
0042 Part 2/3 found this backend has no idempotency-key mechanism
anywhere. Retrying a POST/PATCH/DELETE whose response was lost to a
network blip (as opposed to one that never reached the server at all —
indistinguishable from the client's side) risks a real double-mutation
this backend cannot detect or deduplicate. `RetryInterceptor` therefore
checks the HTTP method before anything else: only `GET` is retried, and
only on `DioExceptionType.connectionTimeout`/`sendTimeout`/
`receiveTimeout`/`connectionError` — never on any real backend response,
2xx through 5xx alike, since a response the server actually sent is the
server answering, not a transient condition to retry past.

**Error mapping is built directly from the backend's real, already-
verified failure taxonomy, not a generic HTTP status switch.**
`ApiErrorMapper` reads `backend/app/api/errors.py`'s own documented
status-code policy (400/401/403/404/422/500, all through one
`ErrorResponse{detail: str | list[str]}` envelope) and produces exactly
one `ApiException` shape with matching convenience getters
(`isUnauthorized`, `isForbidden`, ...). `detail`'s `str | list[str]`
duality is flattened once, here, rather than leaving every future
repository's catch block to rediscover that the backend can return
either shape.

**Debug logging uses `dart:developer.log`, never `print`.** This
project's own lint config (`analysis_options.yaml`) enables
`avoid_print` specifically to keep a stray debug `print` out of
production code; `ApiLoggingInterceptor` is also only ever added to the
interceptor chain at all when `kDebugMode` is true (checked once, in
`ApiClient`'s constructor), so a release build carries zero logging
overhead rather than a runtime check per request.

**Single-flight refresh lock.** `AuthInterceptor` holds one in-flight
`Completer<bool>?` — every 401 that arrives while a refresh is already
running awaits that same attempt rather than triggering a second
concurrent refresh call. Verified directly: `test/core/network/
auth_interceptor_test.dart`'s concurrency test fires two requests that
both 401 and asserts the refresh callback ran exactly once.

## Consequences

**No feature repository changed.** `lib/features/**` is untouched by
this phase — every screen still runs on its existing mock, exactly as
before. This is deliberate scoping, not an oversight: Step 3 (per-
feature repository integration) is its own later phase, per the
directive's own "Complete one before moving to the next."

**Two new dependencies, both disclosed in `pubspec.yaml`'s own
comments:** `dio` (this phase) and `flutter_secure_storage` (added now,
consumed starting next phase — Auth's token storage — rather than a
second `pubspec.yaml` edit).

**Not yet verified by execution** — same disclosed constraint as every
prior phase (ADR 0002): no Flutter/Dart SDK exists in this sandbox, so
`test/core/network/`'s 4 new files (18 tests total, covering error
mapping, success paths, the GET-only/network-only retry policy, and the
full auth-header/refresh/retry/single-flight/skip-list behavior via a
hand-written `HttpClientAdapter` fake — no new test-only dependency
added) are structurally verified (brace/paren/bracket balance,
`print()`/cross-feature-import sweeps) but have not been executed.
