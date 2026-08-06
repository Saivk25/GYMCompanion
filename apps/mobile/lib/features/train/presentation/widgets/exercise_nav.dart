import 'package:flutter/material.dart';

import '../../../../design/design.dart';
import '../../domain/train_models.dart';

/// A compact, horizontally-scrolling exercise switcher for the Active
/// Workout screen (UX/UI Design Bible: "compact exercise nav"). Not
/// [AppSegmentedControl] — that component's segments are always equally
/// weighted and non-scrolling (right for 2-4 fixed tabs); a session can
/// have more exercises than comfortably fit as equal-width segments, and
/// each one also needs a completion signal, which a segmented control's
/// vocabulary has no room for. Scoped to this screen rather than the
/// design system: a single, narrow use case today, not yet a pattern
/// repeated elsewhere.
class ExerciseNav extends StatelessWidget {
  const ExerciseNav({
    required this.performances,
    required this.selectedIndex,
    required this.onSelect,
    super.key,
  });

  final List<TrainExercisePerformance> performances;
  final int selectedIndex;
  final ValueChanged<int> onSelect;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 40,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: performances.length,
        separatorBuilder: (_, __) => const SizedBox(width: AppSpacing.sm),
        itemBuilder: (BuildContext context, int index) {
          final TrainExercisePerformance perf = performances[index];
          final bool isSelected = index == selectedIndex;
          return _NavChip(
            label: perf.exerciseName,
            isSelected: isSelected,
            isComplete: perf.isComplete,
            onTap: () => onSelect(index),
          );
        },
      ),
    );
  }
}

class _NavChip extends StatelessWidget {
  const _NavChip({
    required this.label,
    required this.isSelected,
    required this.isComplete,
    required this.onTap,
  });

  final String label;
  final bool isSelected;
  final bool isComplete;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final AppSemanticColors semantic = Theme.of(context).semanticColors;
    final TextTheme textTheme = Theme.of(context).textTheme;

    final Color background = isSelected ? semantic.selectedContainer : colorScheme.surfaceContainerHighest;
    final Color foreground = isSelected ? semantic.selected : colorScheme.onSurfaceVariant;

    return Semantics(
      button: true,
      selected: isSelected,
      label: isComplete ? '$label, completed' : label,
      child: Material(
        color: background,
        borderRadius: AppRadius.radiusFull,
        child: InkWell(
          onTap: onTap,
          borderRadius: AppRadius.radiusFull,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: AppSpacing.sm),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                if (isComplete) ...<Widget>[
                  Icon(AppIcons.successFilled, size: 14, color: semantic.success),
                  const SizedBox(width: AppSpacing.xs),
                ],
                Text(label, style: textTheme.labelMedium?.copyWith(color: foreground)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
