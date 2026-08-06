import 'package:flutter/material.dart';

import '../tokens/app_typography.dart';

/// Builds a full [TextTheme] from [AppTypography]'s geometry-only styles,
/// applying the correct color for [colorScheme].
///
/// [AppTypography]'s styles deliberately carry no color — a type scale is
/// about size, weight, and rhythm, not brightness, and baking a color into
/// a token used by both themes would make the token itself theme-aware in
/// a way that invites exactly the kind of light/dark inconsistency a
/// shared token system exists to prevent. This file is the one place
/// geometry and color combine into the [TextStyle] values Flutter widgets
/// actually read from `Theme.of(context).textTheme`.
///
/// Two foreground colors are used, matching how Material itself
/// distinguishes primary from secondary text: [ColorScheme.onSurface] for
/// every reading-weight style (display/headline/title/body — the text a
/// screen exists to communicate), and [ColorScheme.onSurfaceVariant] for
/// label styles (buttons, chips, captions, timestamps) — text that is
/// present but should never visually compete with the content it
/// describes. This is a real, considered use of two tones, not zero
/// (flat, no hierarchy) or five (arbitrary).
abstract final class AppTextTheme {
  static TextTheme build(ColorScheme colorScheme) {
    final Color primaryText = colorScheme.onSurface;
    final Color secondaryText = colorScheme.onSurfaceVariant;

    return TextTheme(
      displayLarge: AppTypography.displayLarge.copyWith(color: primaryText),
      displayMedium: AppTypography.displayMedium.copyWith(
        color: primaryText,
      ),
      displaySmall: AppTypography.displaySmall.copyWith(color: primaryText),
      headlineLarge: AppTypography.headlineLarge.copyWith(
        color: primaryText,
      ),
      headlineMedium: AppTypography.headlineMedium.copyWith(
        color: primaryText,
      ),
      headlineSmall: AppTypography.headlineSmall.copyWith(
        color: primaryText,
      ),
      titleLarge: AppTypography.titleLarge.copyWith(color: primaryText),
      titleMedium: AppTypography.titleMedium.copyWith(color: primaryText),
      titleSmall: AppTypography.titleSmall.copyWith(color: primaryText),
      bodyLarge: AppTypography.bodyLarge.copyWith(color: primaryText),
      bodyMedium: AppTypography.bodyMedium.copyWith(color: primaryText),
      bodySmall: AppTypography.bodySmall.copyWith(color: secondaryText),
      labelLarge: AppTypography.labelLarge.copyWith(color: primaryText),
      labelMedium: AppTypography.labelMedium.copyWith(color: secondaryText),
      labelSmall: AppTypography.labelSmall.copyWith(color: secondaryText),
    );
  }
}
