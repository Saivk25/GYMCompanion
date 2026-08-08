# ADR 0047: Readiness repository integration — Step 3, feature 2

- Status: accepted
- Date: 2026-08-08

## Context

Step 3 of `docs/adr/0042-production-integration-plan.md`'s second
feature: replace `MockReadinessRepository` with a real, backend-backed
`ApiReadinessRepository`, reusing `docs/adr/0045`'s shared mapping
convention exactly as established — no feature-specific mapping
utilities were introduced. Unlike Today, `ReadinessRepository`'s
existing interface (`fetchHome`/`submitCheckIn`) maps onto real backend
endpoints field-for-field with no shape mismatch: `ReadinessEntry`
already mirrors `ReadinessResponse` exactly (its own doc comment said so
before this phase touched it), and `ReadinessHomeViewState` already
modeled "no computed band or score" as its own doc comment's disclosed
gap, matching `docs/adr/0039`'s finding restated in `docs/TECH_DEBT.md`'s
TD-0006.

## Decision

**Two endpoints, no interface change.** `fetchHome()` →
`GET /api/v1/readiness` (`ListReadinessHandler`), the full list, sorted
newest-first client-side (no backend ordering guarantee).
`submitCheckIn(...)` → `POST /api/v1/readiness` (`RecordReadinessHandler`).
No update or delete method was added to `ReadinessRepository`, per the
user's own "keep the repository interface stable where possible"
instruction — no Readiness screen has an edit or delete affordance;
`ReadinessHomeScreen`'s "Edit" action re-opens the check-in flow (a new
`submitCheckIn` call), exactly as it already did against the mock.

**`ReadinessEntryDto` mirrors the full `ReadinessResponse`** — unlike
Today's minimal `ReadinessSummaryDto` (which reads one field), this
module is the real owner of every readiness field, so its DTO carries
all of them, per `docs/adr/0045`'s "a DTO models what a feature
consumes" rule applied to a feature that consumes everything.
`ReadinessSource` gained a `fromWire` factory — the same convention
Auth's `AuthRole`/`AccountStatus` established, reused rather than
inventing a second enum-mapping style, exactly matching the user's
"reuse the shared mapping layer exactly as established" instruction.

**`ReadinessRuleEngine` is never reimplemented or approximated
client-side.** `submitCheckIn`'s real warnings come from `POST
/api/v1/readiness`'s own `IdResponse.warnings` — the exact strings the
real rule engine produced server-side, returned unchanged. Nothing in
`ApiReadinessRepository` inspects a submitted value against a
threshold; the repository is a pure pass-through for whatever the
backend decided.

**`CoachSignalLog`'s warning push is untouched.**
`ReadinessHomeController.submitCheckIn` (`readiness_controller.dart`)
already pushed `result.warnings` into `coachSignalLogProvider` and
already re-fetched `fetchHome()` after a successful submission — the
real "mutate → refetch" pattern this phase's own instruction asks for
was already implemented at the controller level before this
repository existed. No controller code changed; only the repository
underneath it did.

**`submitCheckIn`'s returned `ReadinessEntry` is an honest echo of the
request, not a second fetch.** `POST /api/v1/readiness` returns only
`IdResponse{id, warnings}` (`backend/app/api/schemas/common.py`'s own
"deliberately not the full updated resource" doc comment) — the same
constraint Today's `ApiTodayRepository` never had to face since it has
no mutations. No current caller reads `ReadinessCheckInResult.entry`
(confirmed by reading every Readiness presentation file); building it
from the exact submitted parameters plus the real assigned `id` avoids
a network round trip nothing needs, without fabricating anything —
every field either came from the real response or from what the caller
itself passed in. `source` is echoed as `null`, not `ReadinessSource
.manual`: `submitCheckIn` has no `source` parameter, so the request
body never sends one, and `Readiness.record()`
(`backend/app/domain/readiness/readiness.py`) defaults an omitted
`source` to `None`, confirmed by reading that file directly rather than
assumed. `recordedAt` is a local `DateTime.now()` approximation,
disclosed in the repository's own doc comment as not the authoritative
server timestamp.

**No new backend capability gap was found.** Readiness's own real
fields (sleep, energy, stress, soreness, resting heart rate, HRV) all
map directly; the one gap this feature touches (no computed readiness
band/score) was already found and filed under TD-0006 during Today's
own phase — nothing new to add there.

## Consequences

`MockReadinessRepository` was not deleted — kept as
`test/features/readiness/`'s fixture, doc comment updated to disclose
it is no longer the production implementation (mirroring
`MockTodayRepository`'s own updated doc comment).

Not yet verified by execution — same disclosed constraint as every
prior phase (ADR 0002). `test/features/readiness/
api_readiness_repository_test.dart` (9 tests, against the real
`ApiClient`/`Dio` pipeline via the existing `FakeHttpClientAdapter`) is
structurally verified but not executed.
