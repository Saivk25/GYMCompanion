/// Date/time parsing conventions for every `ApiXRepository`'s DTOs. The
/// backend emits two distinct shapes (`backend/app/api/schemas/*.py`'s
/// own response models), and this file gives each its own named parser
/// so a call site's choice of function documents which shape it expects,
/// rather than every field collapsing into one ambiguous `DateTime.parse`
/// call a reader has to go check the backend schema to disambiguate.
///
/// See `docs/adr/0045-shared-api-mapping-convention.md` for the full
/// DTO/mapping convention this file is one piece of.
library;

/// A `datetime` field (`recorded_at`, `planned_at`, `started_at`,
/// `created_at`, ...) — always emitted via Python's own
/// `datetime.isoformat()`, a timezone-aware ISO 8601 string. Parses it
/// and normalizes to UTC (`.toUtc()`): a backend bug emitting a naive or
/// wrongly-offset timestamp should surface as a wrong *time* the moment
/// it's displayed, never as a wrong *timezone interpretation* silently
/// compounding it further down the mapping pipeline.
DateTime parseApiDateTime(String value) => DateTime.parse(value).toUtc();

/// A `date` field (`planned_date`, `readiness_date`, `session_date`,
/// ...) — a plain `YYYY-MM-DD` calendar date with no time-of-day or
/// timezone component at all (Python's `datetime.date`, via Pydantic's
/// own JSON encoding of it). The `DateTime` this returns is UTC-midnight
/// only as an implementation detail of representing a dateless value in
/// a type that always carries a time component — never compare it
/// against a wall-clock `DateTime.now()` directly. Use [apiDateString]
/// on both sides of a same-day comparison instead (see that function's
/// own doc comment).
DateTime parseApiDate(String value) => DateTime.parse(value);

/// The inverse of [parseApiDate] — formats a device-local calendar date
/// (typically `DateTime.now()`) as the `YYYY-MM-DD` string the
/// backend's own `date` fields use. Every repository that needs to ask
/// "is this record from today" does so by comparing two
/// [apiDateString] outputs, never by comparing raw `DateTime` instants
/// (which would be comparing a dateless calendar value against a
/// timezone-bearing instant — a real, easy-to-miss bug class this
/// function exists specifically to avoid). This is a client-side
/// *filter* over data the backend already returned, never a backend
/// query parameter — see each repository's own doc comment for why
/// (`GET /api/v1/workouts` and `GET /api/v1/readiness` accept no date
/// filter at all; ADR 0042 Part 2's own "no pagination or filtering
/// exists anywhere" finding).
String apiDateString(DateTime date) {
  final String y = date.year.toString().padLeft(4, '0');
  final String m = date.month.toString().padLeft(2, '0');
  final String d = date.day.toString().padLeft(2, '0');
  return '$y-$m-$d';
}
