import 'package:flutter/material.dart';

import '../../../../design/design.dart';

/// A persistent, unobtrusive rest countdown (UX/UI Design Bible Section
/// 5.2: "Persistent, unobtrusive countdown... Skip or let it run") — a
/// slim bar pinned above the primary content, never a full-screen modal
/// or a blocking dialog. The user can keep reading the current exercise
/// (logging the next set, checking cues) while this counts down; it
/// never captures focus or interrupts.
class RestTimerBar extends StatelessWidget {
  const RestTimerBar({required this.secondsRemaining, required this.onSkip, super.key});

  final int secondsRemaining;
  final VoidCallback onSkip;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final TextTheme textTheme = Theme.of(context).textTheme;
    final int minutes = secondsRemaining ~/ 60;
    final int seconds = secondsRemaining % 60;
    final String display = '$minutes:${seconds.toString().padLeft(2, '0')}';

    return Material(
      color: colorScheme.secondaryContainer,
      child: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg, vertical: AppSpacing.sm),
          child: Row(
            children: <Widget>[
              Icon(AppIcons.info, size: 18, color: colorScheme.onSecondaryContainer),
              const SizedBox(width: AppSpacing.sm),
              Expanded(
                child: Text(
                  'Resting — $display',
                  style: textTheme.bodyMedium?.copyWith(color: colorScheme.onSecondaryContainer),
                ),
              ),
              AppButton(
                label: 'Skip',
                variant: AppButtonVariant.tertiary,
                fullWidth: false,
                onPressed: onSkip,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
