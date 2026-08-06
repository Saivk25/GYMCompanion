import 'package:flutter/material.dart';

import '../theme/app_semantic_colors.dart';
import '../tokens/tokens.dart';

/// A small, in-page tab control — the UX/UI Design Bible's own named
/// pattern (Section 4: "In-page tabs: Used within Progress (segmented
/// control across the five dashboards) and within Train (This Week /
/// History / Library)"), specified by name but never actually built as a
/// component before this phase. Per this project's standing rule — "if a
/// required token or component does not exist, extend the design system
/// first, never bypass it" — this is that extension, not a one-off widget
/// built inline inside Train's screen.
///
/// A pill-shaped track containing 2-4 equally-weighted pill segments is
/// deliberately *not* [AppCard] + [AppButton] repurposed: a segmented
/// control's whole visual point is that every option is visible and
/// equally weighted at once (unlike [AppButton]'s "one primary action"
/// hierarchy), and its selected segment is a filled pill *inside* a
/// track, not a card. [AppRadius.full] is used here deliberately — see
/// that token's own doc comment: a segmented control is exactly the
/// "toggle track" case pill shape is reserved for, not a card being
/// given pill corners for decoration.
class AppSegmentedControl<T> extends StatelessWidget {
  const AppSegmentedControl({
    required this.segments,
    required this.selected,
    required this.onChanged,
    super.key,
  });

  /// Each segment as `(value, label)` — 2 to 4 entries in practice
  /// (Progress's five dashboards is the largest case the Bible names).
  final List<(T value, String label)> segments;
  final T selected;
  final ValueChanged<T> onChanged;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final AppSemanticColors semantic = Theme.of(context).semanticColors;

    return DecoratedBox(
      decoration: BoxDecoration(
        color: colorScheme.surfaceContainerHighest,
        borderRadius: AppRadius.radiusFull,
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.xs),
        child: Row(
          children: <Widget>[
            for (final (T value, String label) in segments)
              Expanded(
                child: _Segment<T>(
                  label: label,
                  isSelected: value == selected,
                  onTap: () => onChanged(value),
                  selectedColor: semantic.selectedContainer,
                  selectedForeground: semantic.selected,
                  unselectedForeground: colorScheme.onSurfaceVariant,
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _Segment<T> extends StatelessWidget {
  const _Segment({
    required this.label,
    required this.isSelected,
    required this.onTap,
    required this.selectedColor,
    required this.selectedForeground,
    required this.unselectedForeground,
  });

  final String label;
  final bool isSelected;
  final VoidCallback onTap;
  final Color selectedColor;
  final Color selectedForeground;
  final Color unselectedForeground;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;

    // Semantics.selected announces this as a tab-like control whose
    // current choice a screen reader can state, matching how a native
    // segmented control (UISegmentedControl / Material SegmentedButton)
    // is announced — not merely "button" with no indication of which
    // option is currently active.
    return Semantics(
      button: true,
      selected: isSelected,
      label: label,
      child: ConstrainedBox(
        constraints: const BoxConstraints(minHeight: kMinInteractiveDimension),
        child: Material(
          color: isSelected ? selectedColor : Colors.transparent,
          borderRadius: AppRadius.radiusFull,
          child: InkWell(
            onTap: onTap,
            borderRadius: AppRadius.radiusFull,
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
              child: Center(
                child: Text(
                  label,
                  style: textTheme.labelLarge?.copyWith(
                    color: isSelected ? selectedForeground : unselectedForeground,
                    fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
