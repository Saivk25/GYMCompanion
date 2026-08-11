import 'package:flutter/material.dart';

import '../tokens/app_colors.dart';
import '../tokens/app_opacity.dart';
import 'app_color_scheme.dart';

/// Semantic colors [ColorScheme] has no slot for, plus this app's own
/// named home for **disabled**, **focus**, and **selection** — three
/// states the design system review found were "relying on Flutter
/// defaults" rather than being real, reviewed tokens.
///
/// Material 3's [ColorScheme] already provides `primary`, `secondary`,
/// `tertiary`, `error`, `surface`, `outline`, and their `on*`/container
/// pairs — a real, complete semantic system this app reuses directly
/// rather than duplicating (`danger` in this design system *is*
/// `ColorScheme.error`; there is deliberately no second "danger" token
/// that could drift out of sync with it). What [ColorScheme] has no
/// concept of is **success** and **warning** — states this app needs
/// constantly (a completed session, a reduced-capacity readiness band)
/// that are not "the brand color" and not "an error." [AppSemanticColors]
/// is a [ThemeExtension] that adds exactly those, plus disabled/focus/
/// selection, plus the ordered chart-series palette — nothing that
/// [ColorScheme] already owns.
///
/// ## Disabled, focus, and selection — derived, not invented
///
/// These three are deliberately *not* new hues. Material's own
/// long-standing convention — and the one this design system follows —
/// is that "disabled" always reads as a dimmed [ColorScheme.onSurface]
/// regardless of what element it is disabling (a disabled destructive
/// button is gray, not a faded red), "focus" is [ColorScheme.primary]
/// (the same color that already means "this is interactive/selected"
/// everywhere else in the app), and "selected" reuses
/// [ColorScheme.primaryContainer]/`onPrimaryContainer`. Giving each an
/// explicit, named home here — rather than leaving them as an implicit
/// Material default nothing in this codebase decided — is what makes
/// them reviewable tokens instead of framework behavior leaking through
/// undocumented. [AppOpacity] supplies the actual opacity values (all of
/// them Material 3's own published state-layer numbers), so this class
/// only decides *which color* each state tints, never a new number.
///
/// Because deriving these needs real `Color.withOpacity` arithmetic (not
/// expressible as a `const` literal), [light]/[dark] are `static final`
/// — computed once, on first access, and cached for the app's lifetime,
/// the same "compute once, not on every read" discipline `AppTheme`
/// itself now follows (see that file's own doc comment).
///
/// Each success/warning color follows [ColorScheme]'s own container/
/// on-container pattern (a strong tone for icons/text-on-fill, a soft
/// "container" tone for a badge or banner background, and the correct
/// foreground color for each) — reusing a pattern engineers already know
/// from `colorScheme.primary`/`colorScheme.primaryContainer` rather than
/// inventing a new shape.
///
/// Access via `Theme.of(context).semanticColors` — see
/// `AppSemanticColorsTheme` below.
@immutable
class AppSemanticColors extends ThemeExtension<AppSemanticColors> {
  const AppSemanticColors({
    required this.success,
    required this.onSuccess,
    required this.successContainer,
    required this.onSuccessContainer,
    required this.warning,
    required this.onWarning,
    required this.warningContainer,
    required this.onWarningContainer,
    required this.disabledContent,
    required this.disabledContainer,
    required this.focusRing,
    required this.selected,
    required this.onSelected,
    required this.selectedContainer,
    required this.chartSeries,
    required this.chartReference,
  });

  final Color success;
  final Color onSuccess;
  final Color successContainer;
  final Color onSuccessContainer;

  final Color warning;
  final Color onWarning;
  final Color warningContainer;
  final Color onWarningContainer;

  /// Foreground (text/icon) color for a disabled control — always
  /// [ColorScheme.onSurface] at [AppOpacity.disabledContent], regardless
  /// of the control's own base color. WCAG's non-text contrast
  /// requirement explicitly exempts disabled UI, so this deliberately
  /// does not target a contrast ratio the way every enabled-state color
  /// in this system does — "looks inactive" is the correct signal here,
  /// not "is readable at full strength."
  final Color disabledContent;

  /// Background/fill color for a disabled control's own container (e.g.
  /// a disabled primary button's background) — [ColorScheme.onSurface]
  /// at [AppOpacity.disabledContainer].
  final Color disabledContainer;

  /// The color a visible focus indicator (e.g. a keyboard-navigated
  /// control) tints toward — [ColorScheme.primary], the same color that
  /// already means "interactive" everywhere else, so a focus ring never
  /// introduces a color meaning nothing else in the app has.
  final Color focusRing;

  /// Foreground/background pair for a *selected* control (e.g. a
  /// selected list row, a selected filter chip) — aliases
  /// [ColorScheme.onPrimaryContainer]/`primaryContainer` under this
  /// system's own "Selection" vocabulary, per the Product Bible's
  /// explicit semantic-token list.
  final Color selected;
  final Color onSelected;
  final Color selectedContainer;

  /// An ordered, qualitative palette for distinguishing simultaneous
  /// chart data series. Ordered deliberately: the first series drawn on
  /// any chart should always be `chartSeries[0]`, so the same category
  /// (e.g. "push" volume) reads as the same color across every chart it
  /// appears on, not a color chosen fresh per chart. Exactly three
  /// entries today — see `AppColors.chart1-3`'s own doc comment for why
  /// a larger set was deliberately not built ahead of a real chart
  /// needing it.
  final List<Color> chartSeries;

  /// The color for a structural guideline/threshold line (e.g. a
  /// training-load guardrail ceiling) — neutral, so it reads as
  /// structure, not as another data series.
  final Color chartReference;

  static final AppSemanticColors light = _build(AppColorScheme.light);
  static final AppSemanticColors dark = _build(AppColorScheme.dark);

  static AppSemanticColors _build(ColorScheme scheme) {
    final bool isDark = scheme.brightness == Brightness.dark;
    return AppSemanticColors(
      success: isDark ? AppColors.success300 : AppColors.success500,
      onSuccess: isDark ? AppColors.success900 : AppColors.neutral0,
      successContainer:
          isDark ? AppColors.success900 : AppColors.success100,
      onSuccessContainer:
          isDark ? AppColors.success100 : AppColors.success900,
      warning: isDark ? AppColors.warning300 : AppColors.warning500,
      onWarning: isDark ? AppColors.warning900 : AppColors.neutral0,
      warningContainer:
          isDark ? AppColors.warning900 : AppColors.warning100,
      onWarningContainer:
          isDark ? AppColors.warning100 : AppColors.warning900,
      // ignore: deprecated_member_use
      disabledContent: scheme.onSurface.withOpacity(
        AppOpacity.disabledContent,
      ),
      // ignore: deprecated_member_use
      disabledContainer: scheme.onSurface.withOpacity(
        AppOpacity.disabledContainer,
      ),
      focusRing: scheme.primary,
      selected: scheme.onPrimaryContainer,
      onSelected: scheme.primary,
      selectedContainer: scheme.primaryContainer,
      chartSeries: const <Color>[
        AppColors.chart1,
        AppColors.chart2,
        AppColors.chart3,
      ],
      chartReference:
          isDark ? AppColors.neutral400 : AppColors.chartReference,
    );
  }

  @override
  AppSemanticColors copyWith({
    Color? success,
    Color? onSuccess,
    Color? successContainer,
    Color? onSuccessContainer,
    Color? warning,
    Color? onWarning,
    Color? warningContainer,
    Color? onWarningContainer,
    Color? disabledContent,
    Color? disabledContainer,
    Color? focusRing,
    Color? selected,
    Color? onSelected,
    Color? selectedContainer,
    List<Color>? chartSeries,
    Color? chartReference,
  }) {
    return AppSemanticColors(
      success: success ?? this.success,
      onSuccess: onSuccess ?? this.onSuccess,
      successContainer: successContainer ?? this.successContainer,
      onSuccessContainer: onSuccessContainer ?? this.onSuccessContainer,
      warning: warning ?? this.warning,
      onWarning: onWarning ?? this.onWarning,
      warningContainer: warningContainer ?? this.warningContainer,
      onWarningContainer: onWarningContainer ?? this.onWarningContainer,
      disabledContent: disabledContent ?? this.disabledContent,
      disabledContainer: disabledContainer ?? this.disabledContainer,
      focusRing: focusRing ?? this.focusRing,
      selected: selected ?? this.selected,
      onSelected: onSelected ?? this.onSelected,
      selectedContainer: selectedContainer ?? this.selectedContainer,
      chartSeries: chartSeries ?? this.chartSeries,
      chartReference: chartReference ?? this.chartReference,
    );
  }

  @override
  AppSemanticColors lerp(
    ThemeExtension<AppSemanticColors>? other,
    double t,
  ) {
    if (other is! AppSemanticColors) {
      return this;
    }
    return AppSemanticColors(
      success: Color.lerp(success, other.success, t) ?? success,
      onSuccess: Color.lerp(onSuccess, other.onSuccess, t) ?? onSuccess,
      successContainer:
          Color.lerp(successContainer, other.successContainer, t) ??
              successContainer,
      onSuccessContainer:
          Color.lerp(onSuccessContainer, other.onSuccessContainer, t) ??
              onSuccessContainer,
      warning: Color.lerp(warning, other.warning, t) ?? warning,
      onWarning: Color.lerp(onWarning, other.onWarning, t) ?? onWarning,
      warningContainer:
          Color.lerp(warningContainer, other.warningContainer, t) ??
              warningContainer,
      onWarningContainer:
          Color.lerp(onWarningContainer, other.onWarningContainer, t) ??
              onWarningContainer,
      disabledContent:
          Color.lerp(disabledContent, other.disabledContent, t) ??
              disabledContent,
      disabledContainer:
          Color.lerp(disabledContainer, other.disabledContainer, t) ??
              disabledContainer,
      focusRing: Color.lerp(focusRing, other.focusRing, t) ?? focusRing,
      selected: Color.lerp(selected, other.selected, t) ?? selected,
      onSelected: Color.lerp(onSelected, other.onSelected, t) ?? onSelected,
      selectedContainer:
          Color.lerp(selectedContainer, other.selectedContainer, t) ??
              selectedContainer,
      chartSeries: chartSeries,
      chartReference:
          Color.lerp(chartReference, other.chartReference, t) ??
              chartReference,
    );
  }
}

/// `Theme.of(context).semanticColors` — the idiomatic call site, so a
/// widget never repeats the `.extension<AppSemanticColors>()` lookup
/// inline. `AppTheme` always registers this extension on both the light
/// and dark [ThemeData]; the `AppSemanticColors.light` fallback below
/// only matters for a [ThemeData] built outside `AppTheme` (e.g. a bare
/// `ThemeData()` in an isolated widget test), so a missing extension
/// degrades to a sensible default instead of throwing.
extension AppSemanticColorsTheme on ThemeData {
  AppSemanticColors get semanticColors =>
      extension<AppSemanticColors>() ?? AppSemanticColors.light;
}
