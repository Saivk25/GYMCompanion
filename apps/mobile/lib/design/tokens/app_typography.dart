import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';

/// The type scale — fifteen styles across five families, each family at
/// three sizes. Hierarchy comes from this scale alone: per the UX/UI
/// Design Bible ("Typography should create hierarchy... do not rely on
/// color alone"), no screen should ever lean on font color or a one-off
/// size to distinguish importance when a scale step already exists for
/// that purpose.
///
/// ## Five families, mapped onto Flutter's own vocabulary
///
/// The Bible (Section 10) specifies exactly five named levels — Display,
/// Title, Heading, Body, Caption. Flutter's own Material 3 [TextTheme]
/// already has five families at three sizes each — display, headline,
/// title, body, label — which is the same five-way hierarchy under
/// slightly different names, not a coincidence: it is the same widely-used
/// typographic convention (marketing headline down to fine print) that
/// most professional type systems converge on. Rather than inventing a
/// parallel `AppTextStyles.heading1/heading2/...` vocabulary that
/// shadows Flutter's own and leaves every third-party widget reading the
/// *wrong* one, this file builds real [TextTheme] values — so
/// `Theme.of(context).textTheme.headlineLarge` is correct everywhere,
/// including inside widgets this codebase didn't write. [AppTypography]
/// below is a thin, optional alias layer for call sites that prefer the
/// Bible's own vocabulary (`AppTypography.heading` reads more clearly at
/// a feature-screen call site than `.headlineMedium`), not a second
/// source of truth — every alias simply returns the matching [TextTheme]
/// entry.
///
/// | Bible name | Flutter family | Used for                              |
/// |------------|-----------------|----------------------------------------|
/// | Display    | display         | Rare hero numbers (a big score), onboarding |
/// | Heading    | headline        | Screen and section headings            |
/// | Title      | title           | Card titles, dialog titles, list-section titles |
/// | Body       | body            | Primary reading text                   |
/// | Caption    | label           | Buttons, chips, metadata, timestamps   |
///
/// ## Why no bundled custom font
///
/// Reaching for a Google Font (Inter, Poppins, and similar are the
/// reflexive first choice of most AI-generated and template Flutter UIs)
/// was considered and rejected. The products this system studies for
/// craftsmanship — Apple Health, Apple Fitness, Things 3, Craft — build
/// their entire typographic identity on the *platform's own* system font,
/// executed with real discipline in size, weight, and spacing, not on a
/// bundled third-party typeface. A native system font also has zero
/// licensing, zero bundle-size cost, and (via [_platformFontFamily]) is
/// genuinely native per platform — real SF Pro on iOS/macOS, real Roboto
/// on Android — which a single bundled font can never be on both at once.
/// This is a deliberate, timeless choice, not a placeholder: adding a
/// custom font later is possible, but it should be a considered
/// brand decision made with real specimens in hand, not a default reached
/// for because it was the fastest thing to wire up.
///
/// ## Tabular figures
///
/// The Bible requires "a fixed-width figure treatment" for numbers in
/// data displays "so they don't jitter when they change" — a rep count
/// ticking from 9 to 10 must not shift the layout around it. Ordinary
/// proportional digits (where `1` is narrower than `8`) cause exactly
/// that jitter. [AppTypography.tabular] applies
/// [FontFeature.tabularFigures] (fixed-width digits, a real OpenType
/// feature the system font supports) to any [TextStyle] used for a
/// number that can change in place.
abstract final class AppTypography {
  /// The family name Flutter should ask the OS to resolve.
  ///
  /// `.SF Pro Text`/`.SF Pro Display` are Flutter/Skia's documented,
  /// dot-prefixed aliases for "the current iOS/macOS system font" — a
  /// real font resolved at render time, not a bundled asset. Every other
  /// platform (Android, and any future platform) receives `null`, which
  /// tells Flutter to fall back to its own bundled default (Roboto on
  /// Android) — exactly the native-per-platform behavior described
  /// above. [defaultTargetPlatform] (not `dart:io`'s `Platform`) is used
  /// deliberately: it is the Flutter-idiomatic check, it is overridable
  /// in widget tests, and it does not require a real platform channel to
  /// evaluate.
  static String? get _displayFontFamily {
    switch (defaultTargetPlatform) {
      case TargetPlatform.iOS:
      case TargetPlatform.macOS:
        return '.SF Pro Display';
      case TargetPlatform.android:
      case TargetPlatform.fuchsia:
      case TargetPlatform.linux:
      case TargetPlatform.windows:
        return null;
    }
  }

  static String? get _textFontFamily {
    switch (defaultTargetPlatform) {
      case TargetPlatform.iOS:
      case TargetPlatform.macOS:
        return '.SF Pro Text';
      case TargetPlatform.android:
      case TargetPlatform.fuchsia:
      case TargetPlatform.linux:
      case TargetPlatform.windows:
        return null;
    }
  }

  static TextStyle _display({
    required double fontSize,
    required double height,
    required FontWeight weight,
    required double letterSpacing,
  }) {
    return TextStyle(
      fontFamily: _displayFontFamily,
      fontSize: fontSize,
      height: height / fontSize,
      fontWeight: weight,
      letterSpacing: letterSpacing,
    );
  }

  static TextStyle _text({
    required double fontSize,
    required double height,
    required FontWeight weight,
    required double letterSpacing,
  }) {
    return TextStyle(
      fontFamily: _textFontFamily,
      fontSize: fontSize,
      height: height / fontSize,
      fontWeight: weight,
      letterSpacing: letterSpacing,
    );
  }

  // --- Display — rare hero moments only: a large readiness/score number,
  // an onboarding headline. Heavier weight than Material's own default
  // (400) — a premium data product reads confident numbers as semibold or
  // bolder, never thin. ---
  static TextStyle get displayLarge => _display(
        fontSize: 40,
        height: 48,
        weight: FontWeight.w700,
        letterSpacing: -0.5,
      );
  static TextStyle get displayMedium => _display(
        fontSize: 34,
        height: 40,
        weight: FontWeight.w700,
        letterSpacing: -0.3,
      );
  static TextStyle get displaySmall => _display(
        fontSize: 28,
        height: 36,
        weight: FontWeight.w700,
        letterSpacing: -0.2,
      );

  // --- Headline — screen and section headings. ---
  static TextStyle get headlineLarge => _display(
        fontSize: 24,
        height: 32,
        weight: FontWeight.w700,
        letterSpacing: -0.2,
      );
  static TextStyle get headlineMedium => _display(
        fontSize: 20,
        height: 28,
        weight: FontWeight.w700,
        letterSpacing: -0.1,
      );
  static TextStyle get headlineSmall => _display(
        fontSize: 18,
        height: 24,
        weight: FontWeight.w600,
        letterSpacing: 0,
      );

  // --- Title — card titles, dialog titles, list-section titles. ---
  static TextStyle get titleLarge => _text(
        fontSize: 17,
        height: 24,
        weight: FontWeight.w600,
        letterSpacing: 0,
      );
  static TextStyle get titleMedium => _text(
        fontSize: 15,
        height: 20,
        weight: FontWeight.w600,
        letterSpacing: 0,
      );
  static TextStyle get titleSmall => _text(
        fontSize: 13,
        height: 18,
        weight: FontWeight.w600,
        letterSpacing: 0.1,
      );

  // --- Body — primary reading text. Regular weight, generous line
  // height for sustained readability, per the Bible's "readable at every
  // screen size." ---
  static TextStyle get bodyLarge => _text(
        fontSize: 16,
        height: 24,
        weight: FontWeight.w400,
        letterSpacing: 0,
      );
  static TextStyle get bodyMedium => _text(
        fontSize: 14,
        height: 20,
        weight: FontWeight.w400,
        letterSpacing: 0,
      );
  static TextStyle get bodySmall => _text(
        fontSize: 13,
        height: 18,
        weight: FontWeight.w400,
        letterSpacing: 0.1,
      );

  // --- Label (the Bible's "Caption") — buttons, chips, metadata,
  // timestamps. Semibold, not regular: small text at low weight loses
  // legibility fastest, so label text compensates with weight rather than
  // size. ---
  static TextStyle get labelLarge => _text(
        fontSize: 14,
        height: 20,
        weight: FontWeight.w600,
        letterSpacing: 0.1,
      );
  static TextStyle get labelMedium => _text(
        fontSize: 12,
        height: 16,
        weight: FontWeight.w600,
        letterSpacing: 0.2,
      );
  static TextStyle get labelSmall => _text(
        fontSize: 11,
        height: 14,
        weight: FontWeight.w600,
        letterSpacing: 0.3,
      );

  /// The Bible's own vocabulary, aliased onto the scale above. Every
  /// getter here returns exactly one of the fifteen styles defined above
  /// — never a new value — so there is exactly one place hierarchy is
  /// actually decided.
  static TextStyle get display => displayLarge;
  static TextStyle get heading => headlineMedium;
  static TextStyle get title => titleLarge;
  static TextStyle get body => bodyMedium;
  static TextStyle get caption => labelMedium;

  /// Applies fixed-width digits to [style] for any number that can change
  /// in place (a rep counter, a live timer, a weight input) — see the
  /// class-level doc comment. Non-digit characters in the same [Text]
  /// widget are unaffected; this only changes how digits are spaced.
  static TextStyle tabular(TextStyle style) {
    return style.copyWith(
      fontFeatures: const <FontFeature>[FontFeature.tabularFigures()],
    );
  }
}
