import 'package:flutter/material.dart';

import '../tokens/tokens.dart';

/// The one list-row component this app uses for history, meals,
/// notifications, and every other scrollable list of records. Per the
/// UX/UI Design Bible (Section 10): "Consistent row height and metadata
/// placement across every list... so the user builds one mental model,
/// not five" — explicitly naming "a meal row and a session-history row
/// share the same underlying list-row component" as the standard.
///
/// A fixed slot structure — leading icon, title, optional subtitle,
/// optional trailing content — rather than a free-form `Row` a screen
/// assembles itself, which is what actually enforces "consistent
/// metadata placement": the title is always in the same place relative
/// to the leading icon on every screen, because there is only one
/// component deciding where it goes.
class AppListTile extends StatelessWidget {
  const AppListTile({
    required this.title,
    this.subtitle,
    this.leadingIcon,
    this.trailing,
    this.onTap,
    super.key,
  });

  final String title;
  final String? subtitle;
  final IconData? leadingIcon;

  /// Free-form trailing content — a value, a badge, a chevron. Kept as
  /// a [Widget] rather than a narrower type because the Bible's own
  /// catalog of list uses (history, meals, notifications, PR entries)
  /// legitimately needs different trailing content per context; the
  /// *position and spacing* of that content is what this component
  /// standardizes, not its type.
  final Widget? trailing;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final TextTheme textTheme = Theme.of(context).textTheme;

    final Widget row = Padding(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.lg,
        vertical: AppSpacing.md,
      ),
      child: Row(
        children: <Widget>[
          if (leadingIcon != null) ...<Widget>[
            Icon(leadingIcon, size: 22, color: colorScheme.onSurfaceVariant),
            const SizedBox(width: AppSpacing.md),
          ],
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                Text(title, style: textTheme.titleMedium),
                if (subtitle != null) ...<Widget>[
                  const SizedBox(height: 2),
                  Text(subtitle!, style: textTheme.bodySmall),
                ],
              ],
            ),
          ),
          if (trailing != null) ...<Widget>[
            const SizedBox(width: AppSpacing.md),
            trailing!,
          ],
        ],
      ),
    );

    if (onTap == null) {
      return row;
    }

    return Material(
      color: Colors.transparent,
      child: InkWell(onTap: onTap, child: row),
    );
  }
}
