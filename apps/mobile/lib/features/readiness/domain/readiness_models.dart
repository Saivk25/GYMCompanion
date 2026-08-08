/// Pure Dart value types for the Readiness module — no Flutter import
/// anywhere in this file, matching every other feature's own `domain/`
/// rule. [ReadinessEntry] mirrors `backend/app/api/schemas/readiness.py`'s
/// `ReadinessResponse` field-for-field (`readiness_id, readiness_date,
/// recorded_at, source, sleep_duration_seconds, sleep_quality,
/// energy_level, stress_level, soreness_level, resting_heart_rate,
/// heart_rate_variability, notes, updated_at`), the same fidelity
/// `FuelEntry`/`ProgressEntry` keep with their own backend responses.
library;

/// How a check-in's values were obtained
/// (`backend/app/domain/readiness/enums.py`'s `ReadinessSource`, real —
/// not this client's own invention, unlike `NutritionSource.barcode`
/// which has no route behind it). Every check-in this module creates
/// today is [manual] — there is no wearable sync or import pipeline
/// wired up yet, so [wearable]/[imported] exist here only for API-shape
/// fidelity.
enum ReadinessSource {
  manual,
  wearable,
  imported;

  /// Maps the backend's raw wire string (`"manual"`/`"wearable"`/
  /// `"imported"`) — the `fromWire` convention `docs/adr/0044-
  /// authentication-module.md` established and `docs/adr/0045-shared-
  /// api-mapping-convention.md` named as this project's one enum-mapping
  /// pattern, reused here rather than inventing a second style.
  static ReadinessSource fromWire(String value) {
    return switch (value) {
      'manual' => ReadinessSource.manual,
      'wearable' => ReadinessSource.wearable,
      'imported' => ReadinessSource.imported,
      _ => throw FormatException('Unknown ReadinessSource wire value: $value'),
    };
  }
}

/// One recorded check-in (mirrors `ReadinessResponse` exactly). Every
/// field but the identifiers/timestamps is optional — a check-in with
/// only some data recorded is normal
/// (`Readiness.record()` requires none of them), the same "partial is
/// fine" shape `ProgressEntry` already carries.
///
/// [sleepQuality]/[energyLevel]/[stressLevel]/[sorenessLevel] are all
/// 1-10 self-reported ratings (`backend/app/domain/readiness/
/// value_objects.py`'s shared `_MIN/MAX_SUBJECTIVE_RATING` bound) —
/// deliberately plain `int`, not a shared wrapper type, mirroring the
/// backend's own choice to keep each a distinct value object rather than
/// a generic "bounded int," so a future real repository mapping stays a
/// direct field-for-field translation.
class ReadinessEntry {
  const ReadinessEntry({
    required this.readinessId,
    required this.readinessDate,
    required this.recordedAt,
    this.source,
    this.sleepDuration,
    this.sleepQuality,
    this.energyLevel,
    this.stressLevel,
    this.sorenessLevel,
    this.restingHeartRate,
    this.heartRateVariability,
    this.notes = '',
    this.updatedAt,
  });

  final String readinessId;
  final DateTime readinessDate;
  final DateTime recordedAt;
  final ReadinessSource? source;
  final Duration? sleepDuration;
  final int? sleepQuality;
  final int? energyLevel;
  final int? stressLevel;
  final int? sorenessLevel;
  final double? restingHeartRate;
  final double? heartRateVariability;
  final String notes;
  final DateTime? updatedAt;

  bool get hasAnyData =>
      sleepDuration != null ||
      sleepQuality != null ||
      energyLevel != null ||
      stressLevel != null ||
      sorenessLevel != null ||
      restingHeartRate != null ||
      heartRateVariability != null;
}

/// The result of submitting a check-in: the entry itself, plus whichever
/// real advisory strings `ReadinessRuleEngine` produced for it —
/// `POST /api/v1/readiness`'s own real response shape
/// (`IdResponse.warnings`, formatted by `advisory_warnings()` from the
/// engine's `RuleResult.recommendations`). Genuinely computed server-side
/// from `SleepRule`/`EnergyRule`/`StressRule`/`SorenessRule`/
/// `RecoveryRule` — never fabricated here. [warnings] is `()` when every
/// rule passed, which is not an error — a clean check-in has nothing to
/// recommend.
class ReadinessCheckInResult {
  const ReadinessCheckInResult({required this.entry, this.warnings = const <String>[]});

  final ReadinessEntry entry;
  final List<String> warnings;
}

/// The complete state Readiness Home renders from once its initial fetch
/// has resolved — mirrors `ProgressHomeViewState`'s/`FuelHomeViewState`'s
/// shape (a single page-level `AsyncValue`, no nested per-card status
/// enum).
class ReadinessHomeViewState {
  const ReadinessHomeViewState({
    required this.asOf,
    this.entries = const <ReadinessEntry>[],
    this.hasCheckedInEver = true,
    this.lastCheckInWarnings = const <String>[],
    this.isOffline = false,
  });

  final DateTime asOf;

  /// Every real logged check-in, newest first.
  final List<ReadinessEntry> entries;

  /// `false` only for a brand-new user with no check-in history at
  /// all — distinguishes a genuine first-use empty state from a
  /// returning user simply not having checked in today yet, the same
  /// `hasLoggedAnyMeasurementEver`-shaped distinction Progress's own
  /// Transformation dashboard makes.
  final bool hasCheckedInEver;

  /// The real advisory strings from the most recent submission made
  /// *this session* — transient, not persisted, and not re-derivable
  /// from a plain fetch: `GET`/`list` never return warnings (only a
  /// mutating call does, per `docs/adr/0040-readiness-module.md`), so
  /// this field is genuinely empty again after the next page refresh,
  /// exactly matching what the real backend would let a client know.
  final List<String> lastCheckInWarnings;

  final bool isOffline;

  bool get hasCheckedInToday {
    if (entries.isEmpty) return false;
    final DateTime latest = entries.first.readinessDate;
    return latest.year == asOf.year && latest.month == asOf.month && latest.day == asOf.day;
  }

  ReadinessEntry? get todayEntry => hasCheckedInToday ? entries.first : null;
}
