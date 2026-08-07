/// Shared, pure-Dart domain vocabulary for the Coach module's one real
/// data source — no Flutter import anywhere in this file, matching every
/// other domain file's own rule.
///
/// ## Why this lives in `lib/shared/`, not `lib/features/coach/`
///
/// Every other cross-feature type promoted here ([SessionTier],
/// `NotConnectedPlaceholder`) was promoted *after* a second feature
/// needed something a first feature already had. [CoachSignal] is the
/// opposite direction from day one: Readiness, Fuel, and Train each
/// *produce* one (see their own controllers), and only Coach
/// *consumes* them. A type four features need to import cannot live
/// inside any one of those four features' own folders — including
/// Coach's — without the other three importing across a feature
/// boundary this codebase has never crossed before. `lib/shared/` is
/// the one place already reserved for exactly this "more than one
/// feature genuinely needs this" case.
///
/// ## What a [CoachSignal] actually is, and is not
///
/// Every [CoachSignal] traces back to one real `[severity] message`
/// string returned by the real backend's `advisory_warnings()`
/// (`backend/app/application/shared/advisory_warnings.py`) formatting a
/// real `Recommendation` a real rule engine produced — evaluated
/// server-side, after a real user action (a check-in, a meal log, a
/// completed workout session), and returned as `IdResponse.warnings` on
/// that exact mutating call. [CoachSignal] never carries a confidence
/// score, a rationale beyond [message] itself, or a predictive claim —
/// none of those exist anywhere in the backend's `Recommendation` type
/// (`app/domain/rules/recommendation.py`: severity and a message, and
/// nothing else) — and this type does not invent any. See
/// `docs/adr/0041-coach-module.md` for the full research this type is
/// grounded in.
library;

/// Which real backend rule-engine family produced a [CoachSignal] —
/// deliberately the three the UX/UI Design Bible names for Coach
/// (Recovery/Nutrition/Training Advice), not this codebase's own
/// feature-folder names, because this is a cross-cutting *kind of
/// guidance* label a user reads, not an internal module reference.
///
/// [recovery] <- `ReadinessRuleEngine` (via `ReadinessHomeController
/// .submitCheckIn`). [nutrition] <- `NutritionRuleEngine` (via
/// `FuelHomeController.logMeal`). [training] <- `ProgressiveOverload
/// RuleEngine` + `TrainingLoadRuleEngine` (via `ActiveSessionController
/// .completeSession`). There is deliberately no fourth value for
/// Progress's own `ProgressEvaluationRuleEngine` output or Goal's own
/// `GoalAlignmentRuleEngine` output — the Bible names exactly these
/// three advice categories for Coach, and Progress's/Goal's advisory
/// output does not map cleanly onto any of them (see the ADR's own
/// scope decision).
enum CoachModule {
  recovery,
  nutrition,
  training;

  String get label => switch (this) {
        CoachModule.recovery => 'Recovery',
        CoachModule.nutrition => 'Nutrition',
        CoachModule.training => 'Training',
      };
}

/// Mirrors the backend's own `RecommendationSeverity`
/// (`app/domain/rules/severity.py`) verbatim — four tiers, least to most
/// severe. Never computed or guessed by this client: every [CoachSignal]
/// parses its severity from the real `[severity]` prefix
/// `advisory_warnings()` already writes into every warning string, so a
/// [CoachSeverity] on screen is always a direct read of what the rule
/// engine that produced it actually classified, not a client-side
/// reinterpretation.
enum CoachSeverity {
  info,
  advisory,
  warning,
  critical;

  static CoachSeverity fromToken(String token) => switch (token) {
        'critical' => CoachSeverity.critical,
        'warning' => CoachSeverity.warning,
        'advisory' => CoachSeverity.advisory,
        _ => CoachSeverity.info,
      };

  String get label => switch (this) {
        CoachSeverity.info => 'Info',
        CoachSeverity.advisory => 'Advisory',
        CoachSeverity.warning => 'Warning',
        CoachSeverity.critical => 'Critical',
      };
}

/// One real, already-computed piece of advice — the message half of a
/// real `Recommendation`, plus which [CoachModule] produced it, its real
/// [severity], and when this client received it.
class CoachSignal {
  const CoachSignal({
    required this.id,
    required this.module,
    required this.severity,
    required this.message,
    required this.occurredAt,
  });

  /// Formats and parses the exact `"[severity] message"` shape
  /// `advisory_warnings()` produces (see that function's own docstring:
  /// `f"[{recommendation.severity.value}] {recommendation.message}"`).
  /// A string that doesn't match the expected `[token] ` prefix still
  /// parses — as [CoachSeverity.info] with the whole string kept as
  /// [message] — rather than throwing, since a malformed warning string
  /// should degrade to "shown, least-alarming" rather than crash Coach.
  factory CoachSignal.parse({
    required String id,
    required CoachModule module,
    required String raw,
    required DateTime occurredAt,
  }) {
    final RegExpMatch? match = _prefixPattern.firstMatch(raw);
    if (match == null) {
      return CoachSignal(
        id: id,
        module: module,
        severity: CoachSeverity.info,
        message: raw,
        occurredAt: occurredAt,
      );
    }
    return CoachSignal(
      id: id,
      module: module,
      severity: CoachSeverity.fromToken(match.group(1)!),
      message: match.group(2)!,
      occurredAt: occurredAt,
    );
  }

  static final RegExp _prefixPattern = RegExp(r'^\[(\w+)\]\s*(.+)$');

  final String id;
  final CoachModule module;
  final CoachSeverity severity;
  final String message;
  final DateTime occurredAt;
}
