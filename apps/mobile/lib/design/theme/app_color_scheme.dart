import 'package:flutter/material.dart';

import '../tokens/app_colors.dart';
import '../tokens/app_elevation.dart';

/// Builds this app's [ColorScheme] for light and dark mode from
/// [AppColors] — by hand, field by field, not from
/// [ColorScheme.fromSeed].
///
/// ## Why not `ColorScheme.fromSeed`
///
/// `ColorScheme.fromSeed` (and the `colorSchemeSeed` shortcut on
/// [ThemeData]) is Material's own algorithmic tonal-palette generator —
/// feed it one color, it derives the other ~30 automatically. It is also
/// the single fastest way to make a Flutter app look like every other
/// Flutter app that used it: the derivation is correct and accessible,
/// but it is also generic by construction, because it is designed to
/// produce *a* valid Material palette from *any* input, not *this
/// product's* palette. The placeholder theme this design system replaces
/// (`lib/app.dart`'s original `colorSchemeSeed: const Color(0xFF1F2937)`)
/// was exactly this shortcut — appropriate for the five-tab scaffolding
/// step it was written for (Sprint 1, Step 3), wrong for a production
/// visual identity. Every color below is instead a deliberate,
/// hand-selected value from [AppColors], chosen and justified there.
///
/// ## The neutral ramp, reused and reversed
///
/// Light and dark mode read the *same* [AppColors] neutral ramp in
/// opposite directions (light: low steps for surfaces, high steps for
/// text; dark: the reverse) — the same technique GitHub Primer and
/// Linear use, and the reason switching themes in this app changes
/// brightness without ever feeling like a different product.
abstract final class AppColorScheme {
  static const ColorScheme light = ColorScheme(
    brightness: Brightness.light,
    primary: AppColors.signal500,
    onPrimary: AppColors.neutral0,
    primaryContainer: AppColors.signal100,
    onPrimaryContainer: AppColors.signal900,
    secondary: AppColors.neutral700,
    onSecondary: AppColors.neutral0,
    secondaryContainer: AppColors.neutral100,
    onSecondaryContainer: AppColors.neutral900,
    tertiary: AppColors.signal400,
    onTertiary: AppColors.neutral0,
    tertiaryContainer: AppColors.signal50,
    onTertiaryContainer: AppColors.signal700,
    error: AppColors.danger500,
    onError: AppColors.neutral0,
    errorContainer: AppColors.danger100,
    onErrorContainer: AppColors.danger900,
    surface: AppColors.neutral0,
    onSurface: AppColors.neutral900,
    surfaceContainerHighest: AppColors.neutral100,
    onSurfaceVariant: AppColors.neutral600,
    outline: AppColors.neutral300,
    outlineVariant: AppColors.neutral200,
    shadow: AppColors.neutral900,
    scrim: AppColors.neutral900,
    inverseSurface: AppColors.neutral900,
    onInverseSurface: AppColors.neutral50,
    inversePrimary: AppColors.signal300,
  );

  static const ColorScheme dark = ColorScheme(
    brightness: Brightness.dark,
    primary: AppColors.signal300,
    onPrimary: AppColors.signal900,
    primaryContainer: AppColors.signal800,
    onPrimaryContainer: AppColors.signal100,
    secondary: AppColors.neutral300,
    onSecondary: AppColors.neutral900,
    secondaryContainer: AppColors.neutral800,
    onSecondaryContainer: AppColors.neutral100,
    tertiary: AppColors.signal400,
    onTertiary: AppColors.signal900,
    tertiaryContainer: AppColors.signal900,
    onTertiaryContainer: AppColors.signal100,
    error: AppColors.danger300,
    onError: AppColors.danger900,
    errorContainer: AppColors.danger900,
    onErrorContainer: AppColors.danger100,
    surface: AppColors.neutral1000,
    onSurface: AppColors.neutral50,
    surfaceContainerHighest: AppColors.neutral800,
    onSurfaceVariant: AppColors.neutral400,
    outline: AppColors.neutral700,
    outlineVariant: AppColors.neutral800,
    shadow: AppColors.neutral1000,
    scrim: AppColors.neutral1000,
    inverseSurface: AppColors.neutral50,
    onInverseSurface: AppColors.neutral900,
    inversePrimary: AppColors.signal600,
  );

  /// The surface color a container at [level] should use, for a given
  /// [scheme].
  ///
  /// In light mode this always returns [ColorScheme.surface] — elevation
  /// is communicated by [AppElevation.shadowsFor] alone, since a shadow
  /// reads clearly against a light canvas. In dark mode, where shadows
  /// barely register against a near-black canvas, elevation instead reads
  /// through **surface tint**: each tier's surface is a progressively
  /// lighter step, lerped toward [ColorScheme.surfaceContainerHighest] —
  /// the same "raised surfaces get lighter, not just shadowed" convention
  /// Material 3's own dark-theme guidance establishes, reasoned about
  /// explicitly here rather than left to a framework default. See
  /// `AppElevation`'s class doc comment for the full reasoning.
  static Color surfaceAt(ColorScheme scheme, AppElevationLevel level) {
    if (scheme.brightness == Brightness.light) {
      return scheme.surface;
    }
    switch (level) {
      case AppElevationLevel.flat:
        return scheme.surface;
      case AppElevationLevel.raised:
        return Color.lerp(
              scheme.surface,
              scheme.surfaceContainerHighest,
              0.4,
            ) ??
            scheme.surface;
      case AppElevationLevel.overlay:
        return Color.lerp(
              scheme.surface,
              scheme.surfaceContainerHighest,
              0.75,
            ) ??
            scheme.surfaceContainerHighest;
    }
  }
}
