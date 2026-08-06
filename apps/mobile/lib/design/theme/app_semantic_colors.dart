import 'package:flutter/material.dart';

import '../tokens/app_colors.dart';

/// Semantic colors [ColorScheme] has no slot for.
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
/// is a [ThemeExtension] that adds exactly those two, plus the ordered
/// chart-series palette, and nothing that [ColorScheme] already owns.
///
/// Each semantic color follows [ColorScheme]'s own container/on-container
/// pattern (a strong tone for icons/text-on-fill, a soft "container" tone
/// for a badge or banner background, and the correct foreground color for
/// each) — reusing a pattern engineers already know from `colorScheme.
/// primary`/`colorScheme.primaryContainer` rather than inventing a new
/// shape.
///
/// Access via `Theme.of(context).extension<AppSemanticColors>()!` — see
/// `AppTheme` for where this extension is registered on both the light
/// and dark [ThemeData].
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

  /// An ordered, qualitative palette for distinguishing simultaneous
  /// chart data series. Ordered deliberately: the first series drawn on
  /// any chart should always be `chartSeries[0]`, so the same category
  /// (e.g. "push" volume) reads as the same color across every chart it
  /// appears on, not a color chosen fresh per chart.
  final List<Color> chartSeries;

  /// The color for a structural guideline/threshold line (e.g. a
  /// training-load guardrail ceiling) — neutral, so it reads as
  /// structure, not as another data series.
  final Color chartReference;

  static const AppSemanticColors light = AppSemanticColors(
    success: AppColors.success500,
    onSuccess: AppColors.neutral0,
    successContainer: AppColors.success100,
    onSuccessContainer: AppColors.success900,
    warning: AppColors.warning500,
    onWarning: AppColors.neutral0,
    warningContainer: AppColors.warning100,
    onWarningContainer: AppColors.warning900,
    chartSeries: <Color>[
      AppColors.chart1,
      AppColors.chart2,
      AppColors.chart3,
      AppColors.chart4,
      AppColors.chart5,
    ],
    chartReference: AppColors.chartReference,
  );

  static const AppSemanticColors dark = AppSemanticColors(
    success: AppColors.success300,
    onSuccess: AppColors.success900,
    successContainer: AppColors.success900,
    onSuccessContainer: AppColors.success100,
    warning: AppColors.warning300,
    onWarning: AppColors.warning900,
    warningContainer: AppColors.warning900,
    onWarningContainer: AppColors.warning100,
    chartSeries: <Color>[
      AppColors.chart1,
      AppColors.chart2,
      AppColors.chart3,
      AppColors.chart4,
      AppColors.chart5,
    ],
    chartReference: AppColors.neutral400,
  );

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
