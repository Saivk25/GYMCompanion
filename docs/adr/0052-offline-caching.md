# ADR 0052: Offline caching — Step 4 of production integration

- Status: accepted
- Date: 2026-08-10

## Context

Step 4 of `docs/adr/0042-production-integration-plan.md`'s own "Offline
Strategy" (Part 3), scoped explicitly and narrowly by the user ahead of
implementation:

- A shared local cache layer, reused by every repository — not five
  feature-specific caching mechanisms.
- Read-through caching and stale-while-revalidate for reads.
- Offline reads from the cache when the network is unavailable.
- Existing repository interfaces kept stable wherever possible.
- No mutation retry queues, conflict resolution, background sync,
  optimistic updates, or offline writes — this backend has no
  idempotency-key or synchronization concept for any of those to be
  built against safely (ADR 0042 Part 3's own finding, re-confirmed
  here: `backend/app/api/routes/v1/` has no `Idempotency-Key` handling,
  no ETag/If-Match concurrency control, and no queue/outbox concept
  anywhere in `backend/app/infra/`).
- Any new dependency this needs must be surfaced, with trade-offs,
  before being added.

## Decision

### 1. `shared_preferences` for local persistence, not Hive/Drift/Isar

Surfaced to the user before implementation, per the phase's own
instruction. This app's actual cache shape is a handful of small JSON
view-state blobs (five, one per repository's own `fetchHome()`/
`fetchToday()`), read and written by a single string key, with no
querying, relational, or binary-blob need. `shared_preferences` already
ships as a first-party Flutter plugin with no native schema/migration
step of its own; Hive and Isar add a binary format and adapter-generation
step this app's shape doesn't need, and Drift's relational/SQL layer
would be built for a querying need this cache never has (every read is
"give me the one JSON blob for this key," never a filter, join, or
aggregate query). `flutter_secure_storage` was deliberately not
reconsidered for this — it remains reserved for the one secret this app
persists (the refresh token, `SecureTokenStorage`); this cache holds no
credential or secret, so encryption-at-rest is unnecessary overhead a
plain `shared_preferences` value avoids. The user chose this option
directly when it was presented.

### 2. One shared cache layer (`lib/core/cache/`), not five feature-specific caches

`LocalCache` (`local_cache.dart`) is a thin wrapper around
`SharedPreferences` — `read`/`write`/`invalidate`/`clearAll`, one JSON
envelope shape (`{"cachedAt": "<iso8601>", "data": <raw>}`), one key
prefix. `readThroughCache<T>()` (`read_through_cache.dart`) is the one
generic function implementing read-through + stale-while-revalidate +
offline-fallback, parameterized by a `fetchRawJson`/`build` pair rather
than any one feature's DTOs. Every real repository's own `fetchHome()`/
`fetchToday()` calls this same function; none of the five hand-rolls its
own caching branch logic. This mirrors `docs/adr/0045`'s own "one shared
mapping convention, not five parsing conventions" precedent, applied
here to caching instead of DTO parsing.

### 3. Cache raw JSON, not parsed domain view-states

`fetchRawJson` returns exactly what `ApiClient.get`/`.getList` already
returns from a live call — the same `List<dynamic>`/`Map<String,
dynamic>` shape each repository's own DTO-parsing code already consumed
before this phase, cached unchanged. `build(rawJson, {required
isOffline})` is that same parsing logic, factored out of each
repository's own `fetchHome()` body, called twice: once for a live
response, once for a cached one. The alternative — caching the
constructed `XxxHomeViewState` directly — was rejected because none of
the five domain view-state types has (or needs, for any other reason) a
`toJson`/`fromJson` pair; inventing one on each purely to satisfy a cache
serialization need would be new domain-layer surface area this phase's
own "keep the existing repository interfaces stable wherever possible"
instruction argues against. Caching raw JSON means the *existing*
parsing code remains the only place a view-state is ever constructed,
reused unchanged for both a live and a cached read.

### 4. Stale-while-revalidate means the classic HTTP semantic, not a live mid-session UI push

A cache entry younger than `kCacheFreshDuration` (5 minutes — one
shared constant, not five per-feature tunings, since nothing about this
app's actual data argues for treating one feature's staleness tolerance
differently from another's until real usage data says otherwise) is
returned immediately, and a real background refetch silently refreshes
the cache for the *next* read (`Cache-Control:
stale-while-revalidate`'s own definition). This deliberately does
**not** push a second, fresher value into a screen already rendering
this call's result partway through its lifetime — doing that would
require every `*HomeController.build()` to change shape to accept a
second state emission after its `Future` already resolved (e.g.
`AsyncNotifier` would need to become a `StreamNotifier` or gain a
manual re-emit path), which conflicts directly with this phase's own
"keep existing repository interfaces stable wherever possible"
instruction. This is a disclosed scope line, not a missed enhancement.

### 5. Offline reads fall back to the cache; non-network errors are never masked

`ApiException.isNetworkError` (`statusCode == null` exactly when true)
is the one signal `readThroughCache` uses to decide "the network is
unavailable" versus "the server was reached and rejected this." A
network failure with a cache entry present (however stale) falls back to
it, with `build`'s `isOffline: true` — the exact `XHomeViewState
.isOffline` slot every screen has had, unused, since before any real
repository existed. A network failure with nothing cached rethrows
unchanged (there is nothing to fall back to). A non-network
`ApiException` (a real 4xx/5xx — the server *was* reached) is **never**
masked by a stale cache hit; it rethrows unchanged, matching every prior
phase's "a real app-level error must not be silently hidden behind old
data" posture.

### 6. Cache invalidation on mutation — found and fixed during this phase's own verification, not part of the original design

Self-caught during this phase's own review, before any user-facing
report: introducing the cache changed the meaning of an existing,
already-tested behavior in `ReadinessHomeController.submitCheckIn`,
`FuelHomeController.logMeal`/`.logWater`, and
`ProgressHomeController.logMeasurement`. Each of those controllers
already had a "mutate, then immediately refetch `fetchHome()`" contract,
documented in their own doc comments before this phase
(`FuelHomeController`'s own comment: "appears at the top of today's
list immediately"). Once `fetchHome()` became cached, a refetch that
happened to land within `kCacheFreshDuration` of the *previous* read
would silently take the stale-while-revalidate fast path and return the
pre-mutation list — the just-submitted entry would not appear until the
next natural cache expiry, a real regression this phase's own caching
layer would otherwise have introduced into behavior that worked, and was
tested, before Step 4.

Fixed by adding `LocalCache.invalidate(String key)` — removes exactly
one cache entry — and calling it from the four mutation methods above,
immediately after each real, successful `POST` and before returning:
`ApiReadinessRepository.submitCheckIn`, `ApiFuelRepository.logMeal`/
`.logWater`, `ApiProgressRepository.logMeasurement`. The following
`fetchHome()` call then sees a cold-cache miss and is forced onto the
live-fetch path — the same, already-tested "cold cache fetches live and
writes through" branch `readThroughCache` already had, not a new branch.
No repository interface changed; `invalidate` is called from inside each
repository's own existing mutation method body. `ApiTrainRepository` was
deliberately not touched here: none of its mutations
(`startSession`/`completeSet`/`completeSession`) call `fetchHome()`
afterward (they round-trip through `_fetchFullSession`, a genuinely
different, uncached read), so there was no equivalent regression to fix.

### 7. Pull-to-refresh is a disclosed, different trade-off — not fixed the same way

Every `*HomeController.refresh()` (used for pull-to-refresh and manual
retry) calls the same `Repository.fetchHome()` `build()` does, which
means a pull-to-refresh within `kCacheFreshDuration` of the last read can
also return the still-fresh cached value via the stale-while-revalidate
fast path, rather than guaranteeing a live network round trip. This is
different from Decision 6's bug: it is not stale data masking the
result of an action the user just took, and a background revalidation
is still triggered by the same call. Forcing every pull-to-refresh onto
a true bypass-the-cache live fetch would require adding a
`forceRefresh` parameter to every `Repository.fetchHome()`/`fetchToday()`
signature — a real interface change this phase's own "keep interfaces
stable wherever possible" instruction weighs against, for a UX nicety
(pull-to-refresh already re-syncs at most `kCacheFreshDuration` behind
real state) rather than a correctness bug. Left as a disclosed trade-off
rather than engineered around; see `docs/TECH_DEBT.md` TD-0009 for the
trigger condition under which to revisit it.

### 8. Full cache clear on logout, not per-account key namespacing

`LocalCache.clearAll()` is called once, from
`AuthController._clearLocalSession`, alongside the existing token-storage
clear. Every cached entry is per-account data (workouts, meals,
measurements, check-ins); leaving it behind for the next person signing
into the same device would leak one account's data into another's first,
still-loading frame. A per-user key namespace (e.g. prefixing every cache
key with the signed-in user's id) was considered and rejected as
unnecessary complexity: this is a single-session-at-a-time app with no
multi-account-switch-without-logout feature, so a full clear achieves the
same real guarantee with no new coupling from `lib/core/cache/` to
Auth's own user-id concept.

## Files created

- `apps/mobile/lib/core/cache/local_cache.dart` — `LocalCache`,
  `CacheEntry`, `kCacheFreshDuration`, `sharedPreferencesProvider`,
  `localCacheProvider`.
- `apps/mobile/lib/core/cache/read_through_cache.dart` —
  `readThroughCache<T>()`.
- `apps/mobile/lib/core/cache/cache.dart` — barrel export, mirroring
  `core/network/network.dart`/`core/mapping/mapping.dart`.
- `apps/mobile/test/core/cache/local_cache_test.dart`,
  `apps/mobile/test/core/cache/read_through_cache_test.dart` — the
  shared cache primitives tested in isolation, decoupled from any one
  feature's DTOs.

## Files modified

- `apps/mobile/pubspec.yaml` — added `shared_preferences`.
- `apps/mobile/lib/main.dart` — `main()` is now `async`, awaits
  `SharedPreferences.getInstance()` before `runApp`, and overrides
  `sharedPreferencesProvider`; every real `ApiXRepository.overrideWith`
  now passes `ref.read(localCacheProvider)`.
- `apps/mobile/lib/features/{today,readiness,train,fuel,progress}/
  infrastructure/api_*_repository.dart` — `fetchHome()`/`fetchToday()`
  now delegate to `readThroughCache`; `ApiReadinessRepository
  .submitCheckIn`, `ApiFuelRepository.logMeal`/`.logWater`,
  `ApiProgressRepository.logMeasurement` now call `LocalCache.invalidate`
  on success (Decision 6).
- `apps/mobile/lib/features/auth/application/auth_controller.dart` —
  `_clearLocalSession` now also calls `LocalCache.clearAll()`.
- `apps/mobile/test/features/{today,readiness,train,fuel,progress}/
  api_*_repository_test.dart` — every repository constructor call site
  now supplies a `LocalCache`; each file gained a read-through-cache
  test group (offline fallback, non-network errors never masked,
  stale-while-revalidate) and, for the four mutating repositories, a
  cache-invalidation test group (Decision 6).
- `apps/mobile/test/features/auth/{auth_controller_test.dart,
  auth_flow_test.dart}` — updated for the same `LocalCache` dependency,
  and (in `auth_flow_test.dart`) the logout-clears-cache path.

## Verification performed

No local Flutter SDK is available in this environment (`docs/adr/0002`,
unchanged since every prior phase) — verification here is manual,
structural: every new/modified file re-read in full for import
correctness, constructor-signature agreement between each repository and
its test file, `readThroughCache`'s branch logic traced by hand against
every test case asserting it, and the mutation-invalidation fix (Decision
6) traced end-to-end from each controller's own refetch call through to
`LocalCache.invalidate`. `flutter pub get`/`flutter analyze`/`flutter
test` remain the first real verification this code gets, per ADR 0002 —
unchanged from every prior phase's own disclosure.

## Remaining gaps

- Pull-to-refresh's stale-while-revalidate interaction (Decision 7,
  `docs/TECH_DEBT.md` TD-0009) — disclosed trade-off, not a bug.
- No new backend capability gap was introduced or closed by this phase;
  offline caching is a purely client-side concern layered over the same
  five endpoints Step 3 already integrated against.

## Consequences

Step 4 of `docs/adr/0042-production-integration-plan.md` is complete for
the supportable subset explicitly scoped: read-through caching,
stale-while-revalidate, and offline reads, on one shared layer, with
every repository interface's public signature unchanged. Mutation retry
queues, conflict resolution, background sync, optimistic updates, and
offline writes remain out of scope, per the user's own instruction and
this backend's continued lack of any idempotency/synchronization
concept to build them against safely — unchanged from ADR 0042 Part 3's
original finding.
