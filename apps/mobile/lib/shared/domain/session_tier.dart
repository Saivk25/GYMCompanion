/// Shared, pure-Dart domain vocabulary used by more than one feature.
///
/// [SessionTier] started as a Today-only type (`features/today/domain/
/// today_models.dart`) but Train's Pre-session and Active Workout screens
/// need the exact same three-value vocabulary — the tier chosen (or
/// confirmed) before a session starts is the same tier Today previews.
/// Rather than let Train define a second, semantically-identical enum
/// (exactly the duplication this project's own Train directive calls out:
/// "If duplication appears, improve the component library, not the
/// screen"), this file is the one place both features import from.
library;

/// The three session-intensity defaults `RecoveryState` + time-available
/// resolve to (Domain Model Bible: "selects tier defaults (min/standard/
/// stretch)"). The user may always choose lower than the resolved
/// default, never higher without rule permission.
enum SessionTier {
  min,
  standard,
  stretch;

  /// Bible-facing label — never inferred from the enum name at a call
  /// site, so a rename here cannot silently change what users read.
  String get label => switch (this) {
        SessionTier.min => 'Minimum',
        SessionTier.standard => 'Standard',
        SessionTier.stretch => 'Stretch',
      };

  /// A short, glance-length description of what each tier means in
  /// practice — used where a screen offers an explicit tier choice
  /// (Train's Pre-session screen) rather than only displaying Today's
  /// already-resolved default.
  String get description => switch (this) {
        SessionTier.min => 'Shortest viable version — key lifts only.',
        SessionTier.standard => "Today's full planned session.",
        SessionTier.stretch => 'Extra volume, for when you have more time.',
      };
}
