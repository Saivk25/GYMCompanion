/// Pure Dart value types for the Today hub — no Flutter import anywhere in
/// this file. Per the Clean Architecture separation the Engineering Master
/// Plan requires client-side too: these types describe *what* Today shows,
/// never *how* — `TodayScreen` and its widgets decide rendering; this file
/// only decides shape. Naming mirrors the backend domain (`docs/
/// Gym_Companion_Domain_Model_Decision_Engine_Bible.docx`, Sections 4.8,
/// 4.12, 4.13) deliberately, so a future real `TodayRepository`
/// implementation mapping API responses onto these types is a direct
/// field-for-field translation, not a re-interpretation.
library;

import '../../../shared/domain/session_tier.dart';

export '../../../shared/domain/session_tier.dart' show SessionTier;

/// The rolling recovery band a `RecoveryState` computation resolves to
/// (Domain Model Bible Section 7.3: `Normal -> Light -> Recovery ->
/// Escalate`). Today shows this as a band, never the raw underlying score
/// — per the UX/UI Design Bible's explicit instruction (Section 5.1,
/// "Readiness status as a band (not a raw score by default)").
enum ReadinessBand {
  /// No reduced-capacity signal — the common case, most days.
  normal,

  /// Reduced-capacity signals over the rolling window; caps today's
  /// session tier to standard at most.
  light,

  /// Stronger reduced-capacity signal than [light]; caps today's session
  /// more conservatively still.
  recovery,

  /// A red-flag override (GI symptom or pain flag at/above threshold) or
  /// three consecutive light/recovery days — forces conservative mode and
  /// opens a Safety Escalation case. Today's own job here is only to show
  /// a calm, persistent conservative-mode indicator; the escalation flow
  /// itself is a separate screen (UX/UI Design Bible Section 5, Safety
  /// Escalation), out of this screen's scope.
  escalate,
}

/// Today's session-card sub-state — independent of the page-level fetch
/// lifecycle ([TodayViewState] itself is only ever "loaded" once the
/// initial fetch succeeds). The UX/UI Design Bible describes loading,
/// empty, error, and success as properties of the session card
/// specifically, not of the whole page — a plan-generation failure still
/// leaves the readiness band, streak, and task card fully usable.
enum SessionCardStatus { loading, ready, completed, empty, error }

/// Today's session summary — populated once [SessionCardStatus.ready] or
/// [.completed]. `keyLifts` is intentionally a short, ordered list (the
/// Bible's own "key lifts" phrasing, Section 5.1) — a glance-length
/// preview, not the full exercise list Train's Pre-session screen shows.
class TodaySessionSummary {
  const TodaySessionSummary({
    required this.tier,
    required this.durationEstimateMinutes,
    required this.keyLifts,
    this.oneLineSummary,
  });

  final SessionTier tier;
  final int durationEstimateMinutes;
  final List<String> keyLifts;

  /// The AI's one-sentence phrasing of the day's summary (UX/UI Design
  /// Bible: "AI may phrase the day's summary in one short sentence. It
  /// never initiates a proactive chat bubble here"). `null` renders
  /// nothing — this is flavor, never the only source of the session's
  /// actual facts (tier/duration/lifts are always shown regardless).
  final String? oneLineSummary;
}

/// The understated streak indicator (UX/UI Design Bible: "an understated
/// active-streak indicator"; Domain Model Bible Section 4.12's Habit/
/// Streak). Deliberately thin — this app does not gamify streaks with
/// flame icons or celebratory color (Domain Model Bible: "no shame-framed
/// messaging," applied here to its positive-framing mirror image too;
/// see `TodayScreen`'s own reasoning for why this renders as quiet text,
/// not a badge).
class TodayStreak {
  const TodayStreak({required this.currentDays, required this.graceUsed});

  final int currentDays;

  /// True only while a missed day has been absorbed by the streak's
  /// grace allowance without yet breaking it (Domain Model Bible:
  /// "Grace-used" state) — shown as a quieter qualifier, never a warning.
  final bool graceUsed;
}

/// A single open Task or Recommendation awaiting a response (Domain Model
/// Bible Section 4.13). The UX/UI Design Bible's own phrasing — "*any*
/// open Task or Recommendation" (singular) — is why Today surfaces at
/// most one at a time rather than a list; a second one waits its turn
/// rather than competing for the same slot.
class TodayTask {
  const TodayTask({
    required this.text,
    required this.actionLabel,
    this.rationale,
  });

  /// User-facing text (Domain Model Bible: Task's `user_facing_text`).
  final String text;

  /// The single affirmative action's label (e.g. "Review", "Accept").
  final String actionLabel;

  /// A Recommendation must always carry a rationale (Domain Model Bible,
  /// 4.13's validation rule) — surfaced here as an optional secondary
  /// line so the user always sees *why*, not just *what*.
  final String? rationale;
}

/// The complete state Today's screen renders from, once the initial fetch
/// has resolved. Each field can vary independently — a session-generation
/// failure ([sessionStatus] = [SessionCardStatus.error]) does not block
/// the readiness band, streak, or task card from rendering normally, per
/// the UX/UI Design Bible's explicit "rather than a blocking error
/// screen."
class TodayViewState {
  const TodayViewState({
    required this.date,
    required this.hasActivePlan,
    required this.readinessBand,
    required this.checkInCompletedToday,
    required this.sessionStatus,
    this.session,
    this.streak,
    this.task,
    this.isOffline = false,
  });

  final DateTime date;

  /// `false` only for a brand-new user with no Active Plan yet — Today's
  /// entire empty state (an onboarding-continuation card replaces the
  /// session card) hinges on this single flag, per the UX/UI Design
  /// Bible's Section 5.1 empty-state row.
  final bool hasActivePlan;

  final ReadinessBand readinessBand;

  /// Whether today's readiness check-in has already been submitted. While
  /// `false`, the check-in prompt outranks the session card and renders
  /// above it (UX/UI Design Bible: "A not-yet-completed readiness
  /// check-in outranks it, appearing above the session card").
  final bool checkInCompletedToday;

  final SessionCardStatus sessionStatus;
  final TodaySessionSummary? session;
  final TodayStreak? streak;
  final TodayTask? task;

  /// True when this state is the last-known cached snapshot rather than a
  /// fresh fetch (UX/UI Design Bible: "The last-known cached plan and
  /// check-in status render with a small offline indicator; logging still
  /// works locally").
  final bool isOffline;
}
