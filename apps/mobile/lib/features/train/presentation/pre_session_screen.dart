import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../design/design.dart';
import '../../../shared/domain/session_tier.dart';
import '../../../shared/presentation/app_date_format.dart';
import '../application/train_controller.dart';
import '../domain/train_models.dart';
import 'widgets/tier_picker.dart';

/// Pre-session — UX/UI Design Bible catalog: "Review today's tier before
/// starting. Choose tier and start." A genuine full-screen drill-in (not
/// a tab), so it owns its own [Scaffold] and [AppBar] rather than
/// rendering under [AppShell]'s persistent chrome — see
/// `docs/adr/0037-train-module.md` for why Train's sub-screens are
/// top-level routes on the root navigator, not nested branch routes.
///
/// The "Choose your tier" [TierPicker] is kept even though `StartWorkout
/// SessionRequest` (`backend/app/api/schemas/workout.py`) has no `tier`
/// field to send it to — `ApiTrainRepository.startSession` never
/// transmits the selection. It remains a real, client-side-only control
/// rather than being removed outright, disclosed in `docs/TECH_DEBT.md`
/// (TD-0007) and `docs/adr/0048-train-repository-integration.md` as
/// inert pending a real backend concept of session intensity — distinct
/// from the `estimatedMinutes`/`plannedExerciseNames` fields removed
/// from [TrainWorkout] entirely, since those had no client-only affordance
/// still worth preserving.
class PreSessionScreen extends ConsumerStatefulWidget {
  const PreSessionScreen({required this.workoutId, super.key});

  final String workoutId;

  @override
  ConsumerState<PreSessionScreen> createState() => _PreSessionScreenState();
}

class _PreSessionScreenState extends ConsumerState<PreSessionScreen> {
  SessionTier? _selectedTier;
  bool _isStarting = false;

  @override
  Widget build(BuildContext context) {
    final AsyncValue<TrainWorkout> state =
        ref.watch(preSessionControllerProvider(widget.workoutId));

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(AppIcons.back),
          tooltip: 'Back',
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Pre-session'),
      ),
      body: state.when(
        loading: () => const _PreSessionSkeleton(),
        error: (Object error, StackTrace stackTrace) => Center(
          child: AppErrorState(
            message: "This workout couldn't be loaded.",
            onRetry: () => unawaited(
              ref.read(preSessionControllerProvider(widget.workoutId).notifier)
                  .refresh(widget.workoutId),
            ),
          ),
        ),
        data: (TrainWorkout workout) {
          // `TrainWorkout` no longer carries a `tier` (see `train_models
          // .dart`'s own doc comment — no backend concept to default it
          // from), so the picker's own default, not a workout-derived
          // one, seeds first selection.
          final SessionTier tier = _selectedTier ?? SessionTier.standard;
          return _PreSessionContent(
            workout: workout,
            selectedTier: tier,
            isStarting: _isStarting,
            onTierChanged: (SessionTier t) => setState(() => _selectedTier = t),
            // `_startSession` manages its own loading/error state
            // internally (setState calls inside it), so its Future is
            // deliberately discarded here — the same reviewed,
            // documented pattern `TodayScreen`'s own page-error retry
            // uses (see that file's doc comment on `unawaited_futures`).
            onStart: () => unawaited(_startSession(tier)),
          );
        },
      ),
    );
  }

  Future<void> _startSession(SessionTier tier) async {
    setState(() => _isStarting = true);
    try {
      final String sessionId = await ref
          .read(preSessionControllerProvider(widget.workoutId).notifier)
          .startSession(tier);
      if (!mounted) return;
      context.pushReplacement('/train/session/$sessionId');
    } catch (_) {
      if (!mounted) return;
      setState(() => _isStarting = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Couldn't start the session. Try again.")),
      );
    }
  }
}

class _PreSessionSkeleton extends StatelessWidget {
  const _PreSessionSkeleton();

  @override
  Widget build(BuildContext context) {
    return const SafeArea(
      child: Padding(
        padding: EdgeInsets.all(AppSpacing.lg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            AppSkeletonBox(width: 200, height: 24),
            SizedBox(height: AppSpacing.sm),
            AppSkeletonBox(width: 140, height: 16),
            SizedBox(height: AppSpacing.xxl),
            AppSkeletonBox(width: double.infinity, height: 160),
            SizedBox(height: AppSpacing.xxl),
            AppSkeletonBox(width: double.infinity, height: 48),
          ],
        ),
      ),
    );
  }
}

class _PreSessionContent extends StatelessWidget {
  const _PreSessionContent({
    required this.workout,
    required this.selectedTier,
    required this.isStarting,
    required this.onTierChanged,
    required this.onStart,
  });

  final TrainWorkout workout;
  final SessionTier selectedTier;
  final bool isStarting;
  final ValueChanged<SessionTier> onTierChanged;
  final VoidCallback onStart;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;

    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(AppSpacing.lg),
        children: <Widget>[
          Text(workout.name, style: textTheme.headlineSmall),
          const SizedBox(height: AppSpacing.xs),
          Text(
            appRelativeDay(workout.plannedDate),
            style: textTheme.bodyMedium?.copyWith(color: colorScheme.onSurfaceVariant),
          ),
          if (workout.goal != null) ...<Widget>[
            const SizedBox(height: AppSpacing.md),
            Text(workout.goal!, style: textTheme.bodyMedium),
          ],
          if (workout.notes != null && workout.notes!.isNotEmpty) ...<Widget>[
            const SizedBox(height: AppSpacing.sm),
            Text(
              workout.notes!,
              style: textTheme.bodySmall?.copyWith(color: colorScheme.onSurfaceVariant),
            ),
          ],
          const SizedBox(height: AppSpacing.xxl),
          Text('Choose your tier', style: textTheme.titleMedium),
          const SizedBox(height: AppSpacing.sm),
          TierPicker(selected: selectedTier, onChanged: onTierChanged),
          const SizedBox(height: AppSpacing.xxl),
          AppButton(
            label: 'Start session',
            onPressed: onStart,
            isLoading: isStarting,
          ),
        ],
      ),
    );
  }
}
