import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../design/design.dart';
import '../application/train_controller.dart';
import '../domain/train_models.dart';
import 'widgets/exercise_nav.dart';
import 'widgets/logged_set_row.dart';
import 'widgets/rest_timer_bar.dart';
import 'widgets/session_progress_bar.dart';
import 'widgets/set_input_row.dart';

/// Active Workout — UX/UI Design Bible Section 5.2, the module's single
/// most-specified screen. Bundles what the user's own directive lists
/// separately ("Active Workout / Exercise Logging / Rest Timer / Session
/// Progress") into one screen, because the Bible's own 5.2 spec describes
/// all four as facets of one screen, not four navigable destinations —
/// see `docs/adr/0037-train-module.md` for the full reasoning.
///
/// The rest timer is a persistent [Scaffold.bottomNavigationBar] slot,
/// not a modal — it never blocks the exercise nav, the current
/// exercise's logged sets, or the next set-input row above it.
class ActiveWorkoutScreen extends ConsumerStatefulWidget {
  const ActiveWorkoutScreen({required this.sessionId, super.key});

  final String sessionId;

  @override
  ConsumerState<ActiveWorkoutScreen> createState() => _ActiveWorkoutScreenState();
}

class _ActiveWorkoutScreenState extends ConsumerState<ActiveWorkoutScreen> {
  int _selectedExerciseIndex = 0;
  bool _isEnding = false;

  Timer? _elapsedTicker;
  Duration _elapsed = Duration.zero;
  DateTime? _startedAt;

  Timer? _restTicker;
  int? _restSecondsRemaining;

  static const int _restDurationSeconds = 90;

  @override
  void initState() {
    super.initState();
    _elapsedTicker = Timer.periodic(const Duration(seconds: 1), (_) {
      final DateTime? startedAt = _startedAt;
      if (startedAt == null || !mounted) return;
      setState(() => _elapsed = DateTime.now().difference(startedAt));
    });
  }

  @override
  void dispose() {
    _elapsedTicker?.cancel();
    _restTicker?.cancel();
    super.dispose();
  }

  void _startRest() {
    _restTicker?.cancel();
    setState(() => _restSecondsRemaining = _restDurationSeconds);
    _restTicker = Timer.periodic(const Duration(seconds: 1), (Timer timer) {
      final int? remaining = _restSecondsRemaining;
      if (remaining == null || remaining <= 1) {
        timer.cancel();
        if (mounted) setState(() => _restSecondsRemaining = null);
        return;
      }
      if (mounted) setState(() => _restSecondsRemaining = remaining - 1);
    });
  }

  void _skipRest() {
    _restTicker?.cancel();
    setState(() => _restSecondsRemaining = null);
  }

  Future<void> _logSet(TrainExercisePerformance perf, int setNumber,
      {required double weight, required int reps, required int rpe}) async {
    try {
      await ref.read(activeSessionControllerProvider(widget.sessionId).notifier).logSet(
            exerciseId: perf.exerciseId,
            exerciseName: perf.exerciseName,
            setNumber: setNumber,
            weight: weight,
            reps: reps,
            rpe: rpe,
          );
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Couldn't log that set. Try again.")),
      );
    }
  }

  Future<void> _completeSet(TrainExercisePerformance perf, int setNumber) async {
    try {
      await ref.read(activeSessionControllerProvider(widget.sessionId).notifier).completeSet(
            performanceId: perf.performanceId,
            setNumber: setNumber,
          );
      _startRest();
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Couldn't confirm that set. Try again.")),
      );
    }
  }

  Future<void> _endSession(TrainSession session) async {
    setState(() => _isEnding = true);
    final int totalSets = session.exercisePerformances.fold(
      0, (int sum, TrainExercisePerformance p) => sum + p.sets.length,
    );
    final int completedSets = session.exercisePerformances.fold(
      0, (int sum, TrainExercisePerformance p) => sum + p.sets.where((s) => s.completed).length,
    );
    final double completion = totalSets == 0 ? 0 : (completedSets / totalSets) * 100;
    try {
      await ref.read(activeSessionControllerProvider(widget.sessionId).notifier).completeSession(
            durationSeconds: _elapsed.inSeconds.toDouble(),
            completionPercentage: completion,
          );
      if (!mounted) return;
      context.pushReplacement('/train/session/${widget.sessionId}/summary');
    } catch (_) {
      if (!mounted) return;
      setState(() => _isEnding = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Couldn't end the session. Try again.")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final AsyncValue<TrainSession> state =
        ref.watch(activeSessionControllerProvider(widget.sessionId));

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(AppIcons.back),
          tooltip: 'Back',
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: Text(state.valueOrNull?.workoutName ?? 'Active workout'),
        actions: <Widget>[
          Padding(
            padding: const EdgeInsets.only(right: AppSpacing.lg),
            child: Center(child: Text(_formattedElapsed(_elapsed))),
          ),
        ],
      ),
      bottomNavigationBar: _restSecondsRemaining != null
          ? RestTimerBar(secondsRemaining: _restSecondsRemaining!, onSkip: _skipRest)
          : null,
      body: state.when(
        loading: () => const Center(child: AppLoadingIndicator()),
        error: (Object error, StackTrace stackTrace) => Center(
          child: AppErrorState(
            message: "This session couldn't be loaded.",
            onRetry: () =>
                ref.invalidate(activeSessionControllerProvider(widget.sessionId)),
          ),
        ),
        data: (TrainSession session) {
          _startedAt ??= session.startedAt ?? DateTime.now();

          if (session.status != SessionStatus.active) {
            return Center(
              child: AppEmptyState(
                icon: AppIcons.success,
                title: 'This session has already ended',
                actionLabel: 'View summary',
                onAction: () =>
                    context.pushReplacement('/train/session/${session.sessionId}/summary'),
              ),
            );
          }

          final List<TrainExercisePerformance> performances = session.exercisePerformances;
          if (performances.isEmpty) {
            return const Center(
              child: AppEmptyState(
                icon: AppIcons.train,
                title: 'No exercises in this session',
              ),
            );
          }
          final int index = _selectedExerciseIndex.clamp(0, performances.length - 1);
          final TrainExercisePerformance current = performances[index];
          final int completedExercises = performances.where((p) => p.isComplete).length;

          return SafeArea(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(
                AppSpacing.lg, AppSpacing.lg, AppSpacing.lg, AppSpacing.xxxl,
              ),
              children: <Widget>[
                Text(
                  'Exercise ${index + 1} of ${performances.length}',
                  style: Theme.of(context).textTheme.labelMedium?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                ),
                const SizedBox(height: AppSpacing.xs),
                SessionProgressBar(
                  fraction: performances.isEmpty ? 0 : completedExercises / performances.length,
                ),
                const SizedBox(height: AppSpacing.lg),
                ExerciseNav(
                  performances: performances,
                  selectedIndex: index,
                  onSelect: (int i) => setState(() => _selectedExerciseIndex = i),
                ),
                const SizedBox(height: AppSpacing.xl),
                _ExerciseCard(
                  performance: current,
                  onLog: ({required weight, required reps, required rpe}) => unawaited(
                    _logSet(current, current.sets.length + 1, weight: weight, reps: reps, rpe: rpe),
                  ),
                  onComplete: (int setNumber) => unawaited(_completeSet(current, setNumber)),
                  onViewCues: () => context.push(
                    '/train/exercise/${current.exerciseId}',
                    extra: current.exerciseName,
                  ),
                ),
                const SizedBox(height: AppSpacing.xxl),
                Text(
                  'Logged sets save locally and sync automatically.',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.labelMedium?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                ),
                const SizedBox(height: AppSpacing.lg),
                AppButton(
                  label: 'End session',
                  variant: AppButtonVariant.secondary,
                  isLoading: _isEnding,
                  onPressed: () => unawaited(_endSession(session)),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  static String _formattedElapsed(Duration d) {
    final int minutes = d.inMinutes;
    final int seconds = d.inSeconds % 60;
    return '$minutes:${seconds.toString().padLeft(2, '0')}';
  }
}

class _ExerciseCard extends StatelessWidget {
  const _ExerciseCard({
    required this.performance,
    required this.onLog,
    required this.onComplete,
    required this.onViewCues,
  });

  final TrainExercisePerformance performance;
  final void Function({required double weight, required int reps, required int rpe}) onLog;
  final void Function(int setNumber) onComplete;
  final VoidCallback onViewCues;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final int nextSetNumber = performance.sets.length + 1;

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Row(
            children: <Widget>[
              Expanded(child: Text(performance.exerciseName, style: textTheme.titleLarge)),
              AppButton(
                label: 'Cues',
                variant: AppButtonVariant.tertiary,
                fullWidth: false,
                onPressed: onViewCues,
              ),
            ],
          ),
          if (performance.targetSets != null) ...<Widget>[
            const SizedBox(height: AppSpacing.xs),
            Text(
              'Target: ${performance.targetSets} × ${performance.targetReps}'
              '${performance.targetWeight != null ? ' @ ${performance.targetWeight!.toStringAsFixed(0)}' : ''}',
              style: textTheme.bodySmall?.copyWith(color: colorScheme.onSurfaceVariant),
            ),
          ],
          if (performance.sets.isNotEmpty) ...<Widget>[
            const SizedBox(height: AppSpacing.md),
            for (final TrainExerciseSet set in performance.sets)
              LoggedSetRow(set: set, onComplete: () => onComplete(set.setNumber)),
          ],
          const SizedBox(height: AppSpacing.md),
          SetInputRow(
            key: ValueKey<int>(nextSetNumber),
            setNumber: nextSetNumber,
            suggestedWeight: performance.targetWeight,
            suggestedReps: performance.targetReps,
            onLog: onLog,
          ),
        ],
      ),
    );
  }
}
