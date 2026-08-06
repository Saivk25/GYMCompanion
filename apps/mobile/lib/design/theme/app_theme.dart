import 'package:flutter/material.dart';

import '../tokens/tokens.dart';
import 'app_color_scheme.dart';
import 'app_semantic_colors.dart';
import 'app_text_theme.dart';

/// Assembles every token into the two real [ThemeData] instances this app
/// runs on — [AppTheme.light] and [AppTheme.dark]. This is the single
/// file `MaterialApp.router` (`lib/app.dart`) reads from; no screen or
/// component should construct its own [ThemeData] or override a
/// component's theme locally, per the engineering rule that nothing is
/// hardcoded outside the token/theme layer.
///
/// ## What this file decides beyond color and type
///
/// A [ThemeData] is more than a palette — it is also the default
/// appearance of every built-in Material component (`AppBar`,
/// `NavigationBar`, `Chip`, buttons, dialogs, snack bars). Configuring
/// those defaults here, once, is what lets `lib/shell/app_shell.dart`'s
/// already-existing `AppBar`, `NavigationBar`, and `Chip` inherit this
/// design system's restraint automatically, without that file (or any
/// future feature screen) needing to repeat styling per widget — exactly
/// the "everything must come from design tokens... no duplicated
/// styling" engineering rule applied to Flutter's own component themes,
/// not just to this app's custom ones.
///
/// ## Ripple is deliberately turned off
///
/// Material's default ink-ripple touch feedback is one of the most
/// recognizable "this is an Android Material demo" signals — it is a
/// decorative flourish Android supplies by default, not a considered
/// choice. [splashFactory] is set to [NoSplash.splashFactory] throughout;
/// touch feedback instead comes from each component's own subtle
/// pressed/hover/focus state (opacity or tone shift), which is both
/// calmer and closer to how the products this system studies (Things 3,
/// Craft, Apple Health) actually respond to touch.
abstract final class AppTheme {
  /// `static final`, not a getter — [_build] constructs roughly a dozen
  /// component sub-themes (button styles, input decoration, snack bar,
  /// dialog, bottom sheet, navigation bar...) every time it runs. A
  /// getter re-evaluates its body on *every* access, so anything that
  /// reads `AppTheme.light` more than once — hot reload, a widget
  /// rebuilding above `MaterialApp`, a test constructing it repeatedly —
  /// would silently reallocate the entire theme tree each time, for a
  /// result that is always identical given the same color scheme.
  /// `static final` computes [_build] exactly once, on first access, and
  /// caches the result for the process's lifetime — the same fix, for the
  /// same reason, applied to [AppSemanticColors.light]/`.dark`.
  static final ThemeData light = _build(
    colorScheme: AppColorScheme.light,
    semanticColors: AppSemanticColors.light,
  );

  static final ThemeData dark = _build(
    colorScheme: AppColorScheme.dark,
    semanticColors: AppSemanticColors.dark,
  );

  static ThemeData _build({
    required ColorScheme colorScheme,
    required AppSemanticColors semanticColors,
  }) {
    final TextTheme textTheme = AppTextTheme.build(colorScheme);

    return ThemeData(
      useMaterial3: true,
      brightness: colorScheme.brightness,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: colorScheme.surface,
      textTheme: textTheme,
      splashFactory: NoSplash.splashFactory,
      highlightColor: Colors.transparent,
      extensions: <ThemeExtension<dynamic>>[semanticColors],

      appBarTheme: AppBarTheme(
        backgroundColor: colorScheme.surface,
        foregroundColor: colorScheme.onSurface,
        surfaceTintColor: Colors.transparent,
        elevation: AppElevation.materialElevationFor(AppElevationLevel.flat),
        scrolledUnderElevation: AppElevation.materialElevationFor(
          AppElevationLevel.raised,
        ),
        centerTitle: false,
        titleTextStyle: textTheme.titleLarge,
        iconTheme: IconThemeData(color: colorScheme.onSurface, size: 24),
      ),

      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: colorScheme.surface,
        surfaceTintColor: Colors.transparent,
        indicatorColor: colorScheme.primaryContainer,
        elevation: AppElevation.materialElevationFor(AppElevationLevel.flat),
        height: 64,
        overlayColor: AppOpacity.overlayFor(colorScheme.onSurface),
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          final bool selected = states.contains(WidgetState.selected);
          return textTheme.labelMedium?.copyWith(
            color: selected ? colorScheme.onSurface : colorScheme.onSurfaceVariant,
            fontWeight: selected ? FontWeight.w700 : FontWeight.w600,
          );
        }),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          final bool selected = states.contains(WidgetState.selected);
          return IconThemeData(
            color: selected ? colorScheme.onPrimaryContainer : colorScheme.onSurfaceVariant,
            size: 24,
          );
        }),
      ),

      cardTheme: CardThemeData(
        color: AppColorScheme.surfaceAt(colorScheme, AppElevationLevel.raised),
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: const RoundedRectangleBorder(
          borderRadius: AppRadius.radiusMd,
        ),
      ),

      dividerTheme: DividerThemeData(
        color: colorScheme.outlineVariant,
        thickness: 1,
        space: 1,
      ),

      chipTheme: ChipThemeData(
        backgroundColor: colorScheme.secondaryContainer,
        labelStyle: textTheme.labelMedium?.copyWith(
          color: colorScheme.onSecondaryContainer,
        ),
        side: BorderSide.none,
        shape: const StadiumBorder(),
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md,
          vertical: AppSpacing.xs,
        ),
      ),

      bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: AppColorScheme.surfaceAt(
          colorScheme,
          AppElevationLevel.overlay,
        ),
        surfaceTintColor: Colors.transparent,
        modalElevation: AppElevation.materialElevationFor(
          AppElevationLevel.overlay,
        ),
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(
            top: Radius.circular(AppRadius.lg),
          ),
        ),
        showDragHandle: true,
        dragHandleColor: colorScheme.outline,
      ),

      dialogTheme: DialogThemeData(
        backgroundColor: AppColorScheme.surfaceAt(
          colorScheme,
          AppElevationLevel.overlay,
        ),
        surfaceTintColor: Colors.transparent,
        elevation: AppElevation.materialElevationFor(
          AppElevationLevel.overlay,
        ),
        shape: const RoundedRectangleBorder(
          borderRadius: AppRadius.radiusMd,
        ),
        titleTextStyle: textTheme.headlineSmall,
        contentTextStyle: textTheme.bodyMedium,
      ),

      iconTheme: IconThemeData(color: colorScheme.onSurfaceVariant, size: 24),

      // ## Disabled and interaction states — one source of truth
      //
      // The design system review found disabled styling computed
      // ad hoc per button variant (a hand-rolled `onSurface.withOpacity`
      // pair here, nothing at all on the other two variants) and no
      // pressed/hovered/focused behavior beyond whatever Flutter's
      // `ButtonStyleButton` defaults to internally. All three button
      // themes below now read disabled colors from
      // [AppSemanticColors.disabledContent]/`disabledContainer` — the
      // single named home for "what disabled looks like" — and every
      // variant's `overlayColor` comes from [AppOpacity.overlayFor],
      // this system's own token-driven pressed/hovered/focused state,
      // rather than an unreviewed Material default. Primary
      // (`ElevatedButton`), Secondary (`OutlinedButton`), and Tertiary
      // (`TextButton`) therefore share one disabled/interaction model,
      // varied only by which color each variant's overlay tints toward
      // (its own foreground color), never by whether the states exist.
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: colorScheme.primary,
          foregroundColor: colorScheme.onPrimary,
          disabledBackgroundColor: semanticColors.disabledContainer,
          disabledForegroundColor: semanticColors.disabledContent,
          elevation: 0,
          minimumSize: const Size.fromHeight(48),
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xl),
          shape: const RoundedRectangleBorder(
            borderRadius: AppRadius.radiusSm,
          ),
          textStyle: textTheme.labelLarge,
          animationDuration: AppMotion.fast,
        ).copyWith(
          overlayColor: AppOpacity.overlayFor(colorScheme.onPrimary),
        ),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: colorScheme.onSurface,
          disabledForegroundColor: semanticColors.disabledContent,
          side: BorderSide(color: colorScheme.outline),
          minimumSize: const Size.fromHeight(48),
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xl),
          shape: const RoundedRectangleBorder(
            borderRadius: AppRadius.radiusSm,
          ),
          textStyle: textTheme.labelLarge,
          animationDuration: AppMotion.fast,
        ).copyWith(
          overlayColor: AppOpacity.overlayFor(colorScheme.onSurface),
          side: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.disabled)) {
              return BorderSide(color: semanticColors.disabledContent);
            }
            return BorderSide(color: colorScheme.outline);
          }),
        ),
      ),

      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: colorScheme.primary,
          disabledForegroundColor: semanticColors.disabledContent,
          minimumSize: const Size.fromHeight(48),
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
          shape: const RoundedRectangleBorder(
            borderRadius: AppRadius.radiusSm,
          ),
          textStyle: textTheme.labelLarge,
          animationDuration: AppMotion.fast,
        ).copyWith(
          overlayColor: AppOpacity.overlayFor(colorScheme.primary),
        ),
      ),

      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColorScheme.surfaceAt(
          colorScheme,
          AppElevationLevel.raised,
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.lg,
          vertical: AppSpacing.md,
        ),
        border: OutlineInputBorder(
          borderRadius: AppRadius.radiusSm,
          borderSide: BorderSide(color: colorScheme.outline),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: AppRadius.radiusSm,
          borderSide: BorderSide(color: colorScheme.outline),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: AppRadius.radiusSm,
          borderSide: BorderSide(color: colorScheme.primary, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: AppRadius.radiusSm,
          borderSide: BorderSide(color: colorScheme.error),
        ),
        hintStyle: textTheme.bodyMedium?.copyWith(
          color: colorScheme.onSurfaceVariant,
        ),
        labelStyle: textTheme.bodyMedium?.copyWith(
          color: colorScheme.onSurfaceVariant,
        ),
      ),

      // `inverseSurface`/`onInverseSurface`/`inversePrimary` are
      // `ColorScheme`'s own purpose-built fields for "a surface that
      // deliberately inverts light/dark mode" — exactly what a snack bar
      // is (a dark chip in light mode, a light chip in dark mode). The
      // design system review found an earlier version of this theme
      // hand-picking `AppColors.neutral100`/`neutral900` and re-deriving
      // that same light/dark inversion `AppColorScheme` had already
      // decided — a second, disconnected copy of one decision. Reading
      // `colorScheme.inverseSurface` directly removes the duplication
      // (and the local `isDark` branching it required) in favor of one
      // source of truth.
      snackBarTheme: SnackBarThemeData(
        backgroundColor: colorScheme.inverseSurface,
        contentTextStyle: textTheme.bodyMedium?.copyWith(
          color: colorScheme.onInverseSurface,
        ),
        actionTextColor: colorScheme.inversePrimary,
        behavior: SnackBarBehavior.floating,
        shape: const RoundedRectangleBorder(
          borderRadius: AppRadius.radiusSm,
        ),
      ),
    );
  }
}
