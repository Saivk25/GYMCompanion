/// Pure Dart value types for the Progress module — no Flutter import
/// anywhere in this file, matching every other feature's own `domain/`
/// rule. [ProgressEntry] mirrors `backend/app/api/schemas/progress.py`'s
/// `ProgressResponse` field-for-field (`progress_id, progress_date, unit,
/// source, body_weight, body_fat_percentage, lean_body_mass, muscle_mass,
/// waist, chest, hip, arm, thigh, calf, neck, notes, recorded_at,
/// updated_at`), the same fidelity `FuelEntry` keeps with
/// `NutritionResponse` — a future real `ProgressRepository` mapping API
/// responses onto these types is a direct translation, not a
/// re-interpretation.
///
/// ## Why this file also carries real nutrition/readiness trend types
///
/// [NutritionDayTotal] and [ReadinessDayEntry] are **not** copies of
/// `FuelEntry`/a readiness aggregate — they are Progress's own, narrower
/// view types, each backed by the same real backend concept
/// (`GET /api/v1/nutrition`, `GET /api/v1/readiness`) Fuel's own
/// `FuelEntry` and Today's readiness check-in are backed by, summarized
/// the way a real trend endpoint would summarize them. Progress does not
/// import Fuel's domain layer to build these — that would reach across a
/// feature boundary for a type shaped around Fuel's own screen, not
/// Progress's chart. Each feature owns the view shape its own screens
/// need from a shared underlying aggregate, the same way `MockTrainRepository`
/// and `MockFuelRepository` are independent disclosed mocks despite both
/// ultimately describing the same user's real activity.
library;

/// The eleven loggable body metrics `Progress` carries — every numeric
/// field on the backend's `ProgressResponse` except `progress_id` and its
/// timestamps. Used to identify which metric a trend detail screen is
/// showing and to read that metric off a [ProgressEntry] generically.
enum MeasurementMetric {
  weight,
  bodyFatPercentage,
  leanBodyMass,
  muscleMass,
  waist,
  chest,
  hip,
  arm,
  thigh,
  calf,
  neck;

  String get label => switch (this) {
        MeasurementMetric.weight => 'Weight',
        MeasurementMetric.bodyFatPercentage => 'Body fat',
        MeasurementMetric.leanBodyMass => 'Lean mass',
        MeasurementMetric.muscleMass => 'Muscle mass',
        MeasurementMetric.waist => 'Waist',
        MeasurementMetric.chest => 'Chest',
        MeasurementMetric.hip => 'Hip',
        MeasurementMetric.arm => 'Arm',
        MeasurementMetric.thigh => 'Thigh',
        MeasurementMetric.calf => 'Calf',
        MeasurementMetric.neck => 'Neck',
      };

  /// A disclosed, generic unit suffix — the backend's own `unit` field on
  /// `Progress` lets a user record in metric or imperial, but no such
  /// preference exists anywhere in this client yet (the same gap
  /// `FuelEntry`'s own doc comment discloses for a personalized water
  /// target). `kg`/`cm`/`%` are shown as illustrative units, not read
  /// from a real per-user setting.
  String get unitSuffix => switch (this) {
        MeasurementMetric.weight => 'kg',
        MeasurementMetric.bodyFatPercentage => '%',
        MeasurementMetric.leanBodyMass => 'kg',
        MeasurementMetric.muscleMass => 'kg',
        MeasurementMetric.waist ||
        MeasurementMetric.chest ||
        MeasurementMetric.hip ||
        MeasurementMetric.arm ||
        MeasurementMetric.thigh ||
        MeasurementMetric.calf ||
        MeasurementMetric.neck =>
          'cm',
      };

  /// Reads this metric's value off [entry] — the one place the
  /// enum-to-field mapping is decided, so a trend screen never repeats a
  /// `switch` over every field name itself.
  double? valueFrom(ProgressEntry entry) => switch (this) {
        MeasurementMetric.weight => entry.bodyWeight,
        MeasurementMetric.bodyFatPercentage => entry.bodyFatPercentage,
        MeasurementMetric.leanBodyMass => entry.leanBodyMass,
        MeasurementMetric.muscleMass => entry.muscleMass,
        MeasurementMetric.waist => entry.waist,
        MeasurementMetric.chest => entry.chest,
        MeasurementMetric.hip => entry.hip,
        MeasurementMetric.arm => entry.arm,
        MeasurementMetric.thigh => entry.thigh,
        MeasurementMetric.calf => entry.calf,
        MeasurementMetric.neck => entry.neck,
      };
}

/// One recorded check-in — body composition, circumference measurements,
/// or both at once (mirrors `ProgressResponse` exactly). Recording is a
/// documented append-only policy on the backend, not a domain guard
/// (`docs/adr/0010-progress-immutability-is-a-policy-not-a-guard.md`) —
/// this client only ever creates new entries, never edits one in place,
/// which is consistent with that policy without needing to enforce it
/// itself.
class ProgressEntry {
  const ProgressEntry({
    required this.progressId,
    required this.progressDate,
    required this.recordedAt,
    this.unit,
    this.source,
    this.bodyWeight,
    this.bodyFatPercentage,
    this.leanBodyMass,
    this.muscleMass,
    this.waist,
    this.chest,
    this.hip,
    this.arm,
    this.thigh,
    this.calf,
    this.neck,
    this.notes = '',
    this.updatedAt,
  });

  final String progressId;
  final DateTime progressDate;
  final DateTime recordedAt;
  final String? unit;
  final String? source;
  final double? bodyWeight;
  final double? bodyFatPercentage;
  final double? leanBodyMass;
  final double? muscleMass;
  final double? waist;
  final double? chest;
  final double? hip;
  final double? arm;
  final double? thigh;
  final double? calf;
  final double? neck;
  final String notes;
  final DateTime? updatedAt;

  bool get hasBodyComposition =>
      bodyFatPercentage != null || leanBodyMass != null || muscleMass != null;

  bool get hasCircumferenceMeasurements =>
      waist != null || chest != null || hip != null || arm != null ||
      thigh != null || calf != null || neck != null;
}

/// One day's real, summed nutrition activity — Fuel's own "per-entry log,
/// not a daily rollup" rule (`docs/adr/0011`, backend) applied the same
/// way here: [proteinGrams]/[waterMl] are the sum of that day's real
/// logged `Nutrition` entries, computed client-side over real data, the
/// same legitimate derived-not-fabricated arithmetic `FuelHomeViewState
/// .totalWaterMl` already does for a single day. [metProteinTarget] is
/// derived against [kProteinTargetGrams], a disclosed constant — see that
/// constant's own doc comment.
class NutritionDayTotal {
  const NutritionDayTotal({
    required this.date,
    required this.proteinGrams,
    required this.waterMl,
    required this.hasAnyEntry,
  });

  final DateTime date;
  final double proteinGrams;
  final double waterMl;

  /// `false` for a day with zero logged entries at all — distinct from a
  /// day with entries totalling zero protein, so a chart can render a
  /// true gap instead of a misleading flat zero.
  final bool hasAnyEntry;

  bool get metProteinTarget => hasAnyEntry && proteinGrams >= kProteinTargetGrams;
}

/// A disclosed, generic daily protein target — 130g. No personalized
/// macro target exists anywhere in the domain model yet (there is no
/// such field on `User`/`UserPreferences`, the same gap
/// `_dailyWaterTargetMl` discloses for Fuel's hydration card). It only
/// shapes the reference line/heatmap threshold; the real logged total is
/// never hidden or rounded away.
const double kProteinTargetGrams = 130;

/// One day's real, raw readiness inputs — sleep duration, resting heart
/// rate, and heart-rate variability, the three of `Readiness`'s five
/// recorded fields (`api/schemas/readiness.py`'s `ReadinessResponse`)
/// that chart meaningfully as a trend line (energy/stress/soreness are
/// 1-5 self-report levels, not a continuous quantity a line chart
/// communicates well — they remain visible only via the badge/list
/// treatment on Progress's own Recovery section, not charted here).
/// Deliberately does **not** carry a computed readiness score: the
/// `ReadinessRuleEngine`'s composite score/band exists in the backend
/// domain layer but is not returned by any endpoint yet
/// (`docs/adr/0039-progress-module.md`) — charting only what
/// `ReadinessResponse` actually returns keeps every point here real.
class ReadinessDayEntry {
  const ReadinessDayEntry({
    required this.date,
    required this.hasAnyEntry,
    this.sleepHours,
    this.restingHeartRate,
    this.heartRateVariability,
  });

  final DateTime date;
  final bool hasAnyEntry;
  final double? sleepHours;
  final double? restingHeartRate;
  final double? heartRateVariability;
}

/// The complete state Progress Home renders from once its initial fetch
/// has resolved — mirrors `FuelHomeViewState`'s/`TrainHomeViewState`'s
/// shape (a single page-level `AsyncValue`, no nested per-card status
/// enum).
class ProgressHomeViewState {
  const ProgressHomeViewState({
    required this.asOf,
    this.measurements = const <ProgressEntry>[],
    this.nutritionWeek = const <NutritionDayTotal>[],
    this.readinessWeek = const <ReadinessDayEntry>[],
    this.hasLoggedAnyMeasurementEver = true,
    this.isOffline = false,
  });

  final DateTime asOf;

  /// Real logged check-ins, newest first — enough history (this mock
  /// seeds ~10 weekly entries) to drive both the Transformation summary
  /// card and the full measurement-trend detail screen from the same
  /// list, rather than a second fetch for "more" history.
  final List<ProgressEntry> measurements;

  /// The last 7 days, oldest first — always exactly 7 entries once
  /// loaded (a day with nothing logged is still present, with
  /// [NutritionDayTotal.hasAnyEntry] `false`), so chart/heatmap widgets
  /// never need to pad a shorter list themselves.
  final List<NutritionDayTotal> nutritionWeek;

  /// The last 7 days, oldest first — same shape as [nutritionWeek].
  final List<ReadinessDayEntry> readinessWeek;

  /// `false` only for a brand-new user with no check-in history at
  /// all — distinguishes the Bible's "prompts the first baseline
  /// capture" empty state (Section 15, Progress > Transformation) from
  /// a returning user simply not having logged again yet.
  final bool hasLoggedAnyMeasurementEver;

  final bool isOffline;

  ProgressEntry? get latestMeasurement =>
      measurements.isEmpty ? null : measurements.first;

  bool get hasAnyNutritionHistory =>
      nutritionWeek.any((NutritionDayTotal d) => d.hasAnyEntry);

  bool get hasAnyReadinessHistory =>
      readinessWeek.any((ReadinessDayEntry d) => d.hasAnyEntry);
}
