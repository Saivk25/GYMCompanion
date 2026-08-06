import 'package:flutter/material.dart';

import '../tokens/tokens.dart';

/// A consistent heading + optional trailing action row, used to
/// introduce a section within a screen (e.g. "This Week" above a list,
/// "Recent Activity" above a history preview). Repeating this exact
/// layout by hand on every screen is how heading style and spacing
/// silently drift between screens; [AppSectionHeader] is the one place
/// that layout is decided.
class AppSectionHeader extends StatelessWidget {
  const AppSectionHeader({
    required this.title,
    this.actionLabel,
    this.onActionPressed,
    super.key,
  });

  final String title;

  /// A short trailing text action (e.g. "See all"). `null` renders no
  /// trailing action at all — most section headers have none.
  final String? actionLabel;
  final VoidCallback? onActionPressed;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final TextTheme textTheme = Theme.of(context).textTheme;

    return Padding(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.lg,
        vertical: AppSpacing.sm,
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: <Widget>[
          Text(title, style: textTheme.titleLarge),
          if (actionLabel != null)
            TextButton(
              onPressed: onActionPressed,
              style: TextButton.styleFrom(
                minimumSize: Size.zero,
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.sm,
                  vertical: AppSpacing.xs,
                ),
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                foregroundColor: colorScheme.primary,
              ),
              child: Text(actionLabel!),
            ),
        ],
      ),
    );
  }
}
