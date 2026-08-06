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
  static ThemeData get light => _build(
        colorScheme: AppColorScheme.light,
        semanticColors: AppSemanticColors.light,
      );

  static ThemeData get dark => _build(
        colorScheme: AppColorScheme.dark,
        semanticColors: AppSemanticColors.dark,
      );

  static ThemeData _build({
    required ColorScheme colorScheme,
    required AppSemanticColors semanticColors,
  }) {
    final TextTheme textTheme = AppTextTheme.build(colorScheme);
    final bool isDark = colorScheme.brightness == Brightness.dark;

    return ThemeData(
      useMaterial3: true,
      brightness: colorScheme.brightness,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: colorScheme.surface,
      textTheme: textTheme,
      splashFactory: NoSplash.splashFactory,
      highlightColor: Colors.transparent,
      visualDensity: VisualDensity.standard,
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

      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: colorScheme.primary,
          foregroundColor: colorScheme.onPrimary,
          // ignore: deprecated_member_use
          disabledBackgroundColor: colorScheme.onSurface.withOpacity(0.12),
          // ignore: deprecated_member_use
          disabledForegroundColor: colorScheme.onSurface.withOpacity(0.38),
          elevation: 0,
          minimumSize: const Size.fromHeight(48),
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xl),
          shape: const RoundedRectangleBorder(
            borderRadius: AppRadius.radiusSm,
          ),
          textStyle: textTheme.labelLarge,
          animationDuration: AppMotion.fast,
        ),
      ),

      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: colorScheme.onSurface,
          side: BorderSide(color: colorScheme.outline),
          minimumSize: const Size.fromHeight(48),
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xl),
          shape: const RoundedRectangleBorder(
            borderRadius: AppRadius.radiusSm,
          ),
          textStyle: textTheme.labelLarge,
          animationDuration: AppMotion.fast,
        ),
      ),

      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: colorScheme.primary,
          minimumSize: const Size.fromHeight(48),
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
          shape: const RoundedRectangleBorder(
            borderRadius: AppRadius.radiusSm,
          ),
          textStyle: textTheme.labelLarge,
          animationDuration: AppMotion.fast,
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

      snackBarTheme: SnackBarThemeData(
        backgroundColor: isDark ? AppColors.neutral100 : AppColors.neutral900,
        contentTextStyle: textTheme.bodyMedium?.copyWith(
          color: isDark ? AppColors.neutral900 : AppColors.neutral50,
        ),
        actionTextColor: isDark ? AppColors.signal600 : AppColors.signal300,
        behavior: SnackBarBehavior.floating,
        shape: const RoundedRectangleBorder(
          borderRadius: AppRadius.radiusSm,
        ),
      ),
    );
  }
}
