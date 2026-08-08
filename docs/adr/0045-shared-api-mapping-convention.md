# ADR 0045: Shared API mapping convention

- Status: accepted
- Date: 2026-08-08

## Context

Step 3 of `docs/adr/0042-production-integration-plan.md` replaces six
mock repositories (Today, Readiness, Train, Fuel, Progress, Coach) with
real, backend-backed ones, one at a time. Before writing the first one
(`ApiTodayRepository`), the driving directive asked for one shared
mapping convention every later `ApiXRepository` follows, so six
independent repositories don't each invent their own JSON-parsing,
enum-mapping, and date-handling style — the same "establish once, reuse
six times" reasoning `docs/adr/0043-core-networking-layer.md` already
applied to the transport layer itself.

## Decision

**`lib/core/mapping/` is `lib/core/network/`'s sibling, not a layer on
top of it.** `core/network/` maps *transport* failures (HTTP/`dio`
errors) into one `ApiException` shape. `core/mapping/` maps a
*successful* response's already-decoded JSON into this app's DTOs, and
from there into domain models. Two distinct concerns, kept in two
distinct, equally small folders — `core/mapping/json_field.dart`
(typed field extraction) and `core/mapping/api_date_time.dart`
(date/time parsing), both exported from `core/mapping/mapping.dart`.

**DTO organization and naming.** Each feature's infrastructure layer
gets its own `dto/` subfolder: `lib/features/<feature>/infrastructure/
dto/<thing>_dto.dart`. One class per backend response shape the feature
actually consumes, named `<Thing>Dto` — deliberately close to the
backend's own `<Thing>Response`/`<Thing>DTO` naming
(`backend/app/api/schemas/*.py` / `backend/app/application/*/dto/`) so
mapping a field is a direct, checkable translation against the backend
source, never a re-interpretation. A DTO is infrastructure-only and
never imported by `domain/`, `application/`, or `presentation/` — the
same layering `today_models.dart`'s own doc comment already established
before any real DTO existed, applied literally now that one does.

**A DTO models the fields a feature actually consumes, not necessarily
the backend's complete response envelope.** `WorkoutResponse` has eleven
fields; if a feature only ever reads four of them, its DTO declares
four fields, not eleven placeholders for values nothing uses. Every
field it *does* declare still maps directly and honestly from the named
backend field — this is an omission of the unused, never a
reinterpretation of the used.

**JSON (de)serialization: typed extraction, not ad hoc casts.**
`json['x'] as T` scattered across `fromJson` constructors fails with a
cryptic, field-less error the moment a backend response drifts.
`core/mapping/json_field.dart`'s `JsonFieldExtraction` extension on
`Map<String, dynamic>` (`requireString`/`requireInt`/`requireDouble`/
`requireBool`/`requireList`/`requireObject`, and an `optional*` variant
of each) is what every DTO's `factory X.fromJson(Map<String, dynamic>
json)` uses instead — a missing or wrongly-typed field fails once, with
the field name and the offending object attached, rather than as an
opaque type-cast exception several stack frames removed from which
field caused it.

**Domain model mapping lives on the DTO itself, not a separate mapper
class.** A `toDomain()` instance method (or, where a DTO's fields don't
map 1:1 onto a single domain type, a small top-level function in the
same file) does the translation. No `XMapper` indirection layer — this
project's own established "no unnecessary indirection" posture (mirrored
in, e.g., `ApiAuthRepository`'s single `_tokensFromJson` helper) applied
consistently here; a DTO and its own mapping are one small, colocated
unit, not two files a reader has to cross-reference.

**Enum mapping reuses the `fromWire` pattern `docs/adr/0044-
authentication-module.md` already established** (`AuthRole.fromWire`,
`AccountStatus.fromWire`) — a static factory per client-side enum that
takes the backend's raw wire string and throws a clear `FormatException`
on an unrecognized value, rather than silently mapping an unknown value
to some default. No new utility needed; this ADR just names it as the
one convention every future enum mapping follows, rather than each
feature reinventing its own switch-with-a-fallback.

**Date/time parsing: two named functions, chosen by which backend shape
a field actually is, never one ambiguous `DateTime.parse`.**
`parseApiDateTime` for a real `datetime` field (backend's
`datetime.isoformat()` — timezone-aware, normalized to UTC on parse).
`parseApiDate` for a bare `date` field (`YYYY-MM-DD`, no time-of-day or
timezone at all). `apiDateString` is the inverse of `parseApiDate`, for
the one recurring client-side need every list-returning, non-filterable
endpoint creates: "does this record belong to today" — computed by
comparing two `apiDateString` outputs, never by comparing a dateless
calendar value against a wall-clock `DateTime.now()` instant directly
(a real, easy-to-miss bug class this function exists specifically to
prevent).

**Shared API error mapping is not a new thing this ADR introduces** —
`ApiErrorMapper`/`ApiException` (`docs/adr/0043`) already is it. Every
`ApiXRepository` lets a thrown `ApiException` propagate out of its
methods unchanged; nothing in `core/mapping/` re-wraps or duplicates
that mapping.

**Reusable mapper utilities are exactly the two files above — no more,
no less, deliberately.** A third utility (e.g. a generic `List<T>
mapJsonList<T>(...)`) was considered and left out: `core/mapping/`'s own
job is making field-level extraction and date parsing safe and
consistent, not building a generic serialization framework this
codebase has never needed elsewhere. If a real third cross-cutting need
emerges once a second or third `ApiXRepository` is built, it gets added
then, against a real second caller — the same "don't extract
speculatively" discipline `docs/TECH_DEBT.md`'s TD-0001 resolution
already modeled for this project.

**Every real (non-Auth) `ApiXRepository` prefixes its paths with
`ApiConfig.v1PathPrefix`** (`/api/v1`) — `ApiAuthRepository` is the one
exception, using `ApiConfig.authPathPrefix` (`''`, root-level), per
`backend/app/main.py`'s own router mounting. This was implicit in
`ApiConfig`'s own existing doc comment; this ADR states it explicitly as
the convention every Step-3 repository follows.

## Consequences

`ApiTodayRepository` (this same phase) is the first real consumer,
proving the convention against a genuine caller rather than only
against itself. `core/mapping/` has its own unit tests
(`test/core/mapping/`), independent of any one feature's repository
tests, matching `test/core/network/`'s own precedent of testing the
shared layer once rather than through every repository that uses it.

No existing file changed as a result of this ADR alone — `lib/core/
mapping/` is new, additive infrastructure; `ApiTodayRepository`'s own
files are where it is first exercised, documented in that phase's own
report.
