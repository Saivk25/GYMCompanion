import '../../../shared/domain/session_tier.dart';
import '../application/train_controller.dart';
import '../domain/train_models.dart';

/// A placeholder [TrainRepository] — the same disclosed-limitation
/// posture `MockTodayRepository` established (ADR 0036, Decision 2),
/// applied here to Train. Every method below returns realistic, fixed
/// (or session-mutated in-memory) data instead of a real network call;
/// an authenticated HTTP client mapping onto
/// `backend/app/api/routes/v1/workout.py`'s real endpoints is a later,
/// separately-scoped stage, not something this module's build absorbs
/// speculatively.
///
/// Unlike [MockTodayRepository] (pure read, never mutated),
/// [logSet]/[completeSet]/[completeSession] genuinely mutate an in-memory
/// session store — the Active Workout screen needs to see its own logged
/// sets reflected back, and a mock that always returned the same fixed
/// snapshot regardless of what was just logged would make that screen
/// impossible to honestly develop or test against. This is still fully
/// disclosed: state lives only for the app's process lifetime, in a
/// private `Map`, never persisted — restarting the app resets it.
class MockTrainRepository implements TrainRepository {
  MockTrainRepository() : _sessions = <String, TrainSession>{};

  final Map<String, TrainSession> _sessions;
  bool _hasShownIllustrativeWarnings = false;

  static const List<String> _standardLifts = <String>[
    'Back Squat',
    'Bench Press',
    'Barbell Row',
  ];

  @override
  Future<TrainHomeViewState> fetchHome() async {
    await _delay();
    return TrainHomeViewState(
      status: TrainHomeStatus.ready,
      thisWeek: <TrainWorkout>[
        TrainWorkout(
          workoutId: 'workout-today',
          name: 'Upper Body Strength',
          plannedDate: DateTime.now(),
          status: WorkoutStatus.planned,
          goal: 'Build pressing strength',
          plannedExerciseNames: _standardLifts,
          tier: SessionTier.standard,
          estimatedMinutes: 45,
        ),
        TrainWorkout(
          workoutId: 'workout-thu',
          name: 'Lower Body Power',
          plannedDate: DateTime.now().add(const Duration(days: 2)),
          status: WorkoutStatus.planned,
          goal: 'Leg drive and hinge strength',
          plannedExerciseNames: const <String>['Deadlift', 'Front Squat', 'Walking Lunge'],
          tier: SessionTier.standard,
          estimatedMinutes: 50,
        ),
        TrainWorkout(
          workoutId: 'workout-sat',
          name: 'Full Body Conditioning',
          plannedDate: DateTime.now().add(const Duration(days: 4)),
          status: WorkoutStatus.planned,
          goal: 'Work capacity',
          plannedExerciseNames: const <String>['Kettlebell Swing', 'Push-Up', 'Row'],
          tier: SessionTier.min,
          estimatedMinutes: 25,
        ),
      ],
      history: <TrainSession>[
        TrainSession(
          sessionId: 'session-past-1',
          workoutId: 'workout-past-1',
          workoutName: 'Upper Body Strength',
          status: SessionStatus.completed,
          sessionDate: DateTime.now().subtract(const Duration(days: 2)),
          completionPercentage: 100,
          rating: 4,
          exercisePerformances: _completedPerformances(),
        ),
        TrainSession(
          sessionId: 'session-past-2',
          workoutId: 'workout-past-2',
          workoutName: 'Lower Body Power',
          status: SessionStatus.completed,
          sessionDate: DateTime.now().subtract(const Duration(days: 5)),
          completionPercentage: 88,
          rating: 3,
          exercisePerformances: _completedPerformances(),
        ),
        TrainSession(
          sessionId: 'session-past-3',
          workoutId: 'workout-past-3',
          workoutName: 'Full Body Conditioning',
          status: SessionStatus.abandoned,
          sessionDate: DateTime.now().subtract(const Duration(days: 9)),
          completionPercentage: 40,
          exercisePerformances: _completedPerformances().take(1).toList(),
        ),
      ],
    );
  }

  @override
  Future<TrainWorkout> fetchWorkout(String workoutId) async {
    await _delay();
    return TrainWorkout(
      workoutId: workoutId,
      name: 'Upper Body Strength',
      plannedDate: DateTime.now(),
      status: WorkoutStatus.planned,
      goal: 'Build pressing strength',
      notes: 'Focus on bar speed for the working sets.',
      plannedExerciseNames: _standardLifts,
      tier: SessionTier.standard,
      estimatedMinutes: 45,
    );
  }

  @override
  Future<TrainSession> startSession(String workoutId, {required SessionTier tier}) async {
    await _delay();
    final String sessionId = 'session-$workoutId-${DateTime.now().millisecondsSinceEpoch}';
    final TrainSession session = TrainSession(
      sessionId: sessionId,
      workoutId: workoutId,
      workoutName: 'Upper Body Strength',
      status: SessionStatus.active,
      sessionDate: DateTime.now(),
      startedAt: DateTime.now(),
      exercisePerformances: _standardLifts
          .asMap()
          .entries
          .map(
            (entry) => TrainExercisePerformance(
              performanceId: 'perf-$sessionId-${entry.key}',
              exerciseId: 'exercise-${entry.key}',
              exerciseName: entry.value,
              sets: const <TrainExerciseSet>[],
              targetSets: 3,
              targetReps: 8,
              targetWeight: 60 + (entry.key * 20),
            ),
          )
          .toList(),
    );
    _sessions[sessionId] = session;
    return session;
  }

  @override
  Future<TrainSession> fetchSession(String sessionId) async {
    await _delay();
    final TrainSession? existing = _sessions[sessionId];
    if (existing != null) {
      return existing;
    }
    // A session reached directly (e.g. from History) rather than via
    // startSession — synthesize a completed one so the summary/detail
    // view still has something real to render.
    final TrainSession fallback = TrainSession(
      sessionId: sessionId,
      workoutId: 'workout-$sessionId',
      workoutName: 'Upper Body Strength',
      status: SessionStatus.completed,
      sessionDate: DateTime.now().subtract(const Duration(days: 1)),
      completionPercentage: 100,
      rating: 4,
      durationSeconds: 2700,
      exercisePerformances: _completedPerformances(),
    );
    _sessions[sessionId] = fallback;
    return fallback;
  }

  @override
  Future<TrainSession> logSet(
    String sessionId, {
    required String exerciseId,
    required String exerciseName,
    required int setNumber,
    required double weight,
    required int reps,
    required int rpe,
  }) async {
    await _delay(short: true);
    final TrainSession current = _sessions[sessionId] ?? await fetchSession(sessionId);

    final List<TrainExercisePerformance> updated = current.exercisePerformances.map((perf) {
      if (perf.exerciseId != exerciseId) {
        return perf;
      }
      final List<TrainExerciseSet> sets = List<TrainExerciseSet>.from(perf.sets)
        ..removeWhere((s) => s.setNumber == setNumber)
        ..add(TrainExerciseSet(
          setNumber: setNumber,
          weight: weight,
          reps: reps,
          rpe: rpe,
          completed: false,
        ))
        ..sort((a, b) => a.setNumber.compareTo(b.setNumber));
      return TrainExercisePerformance(
        performanceId: perf.performanceId,
        exerciseId: perf.exerciseId,
        exerciseName: perf.exerciseName,
        notes: perf.notes,
        sets: sets,
        targetSets: perf.targetSets,
        targetReps: perf.targetReps,
        targetWeight: perf.targetWeight,
      );
    }).toList();

    final TrainSession next = TrainSession(
      sessionId: current.sessionId,
      workoutId: current.workoutId,
      workoutName: current.workoutName,
      status: current.status,
      sessionDate: current.sessionDate,
      exercisePerformances: updated,
      notes: current.notes,
      durationSeconds: current.durationSeconds,
      completionPercentage: current.completionPercentage,
      rating: current.rating,
      startedAt: current.startedAt,
      completedAt: current.completedAt,
      abandonedAt: current.abandonedAt,
    );
    _sessions[sessionId] = next;
    return next;
  }

  @override
  Future<TrainSession> completeSet(
    String sessionId, {
    required String performanceId,
    required int setNumber,
  }) async {
    await _delay(short: true);
    final TrainSession current = _sessions[sessionId] ?? await fetchSession(sessionId);

    final List<TrainExercisePerformance> updated = current.exercisePerformances.map((perf) {
      if (perf.performanceId != performanceId) {
        return perf;
      }
      final List<TrainExerciseSet> sets = perf.sets
          .map((s) => s.setNumber == setNumber ? s.copyWith(completed: true) : s)
          .toList();
      return TrainExercisePerformance(
        performanceId: perf.performanceId,
        exerciseId: perf.exerciseId,
        exerciseName: perf.exerciseName,
        notes: perf.notes,
        sets: sets,
        targetSets: perf.targetSets,
        targetReps: perf.targetReps,
        targetWeight: perf.targetWeight,
      );
    }).toList();

    final TrainSession next = TrainSession(
      sessionId: current.sessionId,
      workoutId: current.workoutId,
      workoutName: current.workoutName,
      status: current.status,
      sessionDate: current.sessionDate,
      exercisePerformances: updated,
      notes: current.notes,
      durationSeconds: current.durationSeconds,
      completionPercentage: current.completionPercentage,
      rating: current.rating,
      startedAt: current.startedAt,
      completedAt: current.completedAt,
      abandonedAt: current.abandonedAt,
    );
    _sessions[sessionId] = next;
    return next;
  }

  @override
  Future<TrainSession> completeSession(
    String sessionId, {
    required double durationSeconds,
    required double completionPercentage,
    int? rating,
  }) async {
    await _delay();
    final TrainSession current = _sessions[sessionId] ?? await fetchSession(sessionId);

    // Two fixed, clearly-illustrative advisory strings on the first
    // completed session only, never a reimplementation of
    // `ProgressiveOverloadRuleEngine`'s/`TrainingLoadRuleEngine`'s real
    // volume/intensity/frequency/progression/deload/acute-load/chronic-
    // load/load-ratio/monotony/strain thresholds — the same disclosed
    // posture `MockReadinessRepository.submitCheckIn` already
    // established; see that file's own doc comment for the full
    // reasoning, which applies unchanged here.
    List<String> warnings = const <String>[];
    if (!_hasShownIllustrativeWarnings) {
      _hasShownIllustrativeWarnings = true;
      warnings = const <String>[
        '[advisory] Example advisory — real recommendations come from the '
            'backend progressive-overload and training-load rule engines '
            'once connected.',
        '[warning] This illustrates where training advice appears; it is '
            'not computed from the session you just completed.',
      ];
    }

    final TrainSession next = TrainSession(
      sessionId: current.sessionId,
      workoutId: current.workoutId,
      workoutName: current.workoutName,
      status: SessionStatus.completed,
      sessionDate: current.sessionDate,
      exercisePerformances: current.exercisePerformances,
      notes: current.notes,
      durationSeconds: durationSeconds,
      completionPercentage: completionPercentage,
      rating: rating,
      startedAt: current.startedAt,
      completedAt: DateTime.now(),
      abandonedAt: current.abandonedAt,
      lastMutationWarnings: warnings,
    );
    _sessions[sessionId] = next;
    return next;
  }

  List<TrainExercisePerformance> _completedPerformances() {
    return _standardLifts.asMap().entries.map((entry) {
      return TrainExercisePerformance(
        performanceId: 'perf-past-${entry.key}',
        exerciseId: 'exercise-${entry.key}',
        exerciseName: entry.value,
        targetSets: 3,
        targetReps: 8,
        targetWeight: 60 + (entry.key * 20),
        sets: List<TrainExerciseSet>.generate(
          3,
          (i) => TrainExerciseSet(
            setNumber: i + 1,
            weight: 60 + (entry.key * 20),
            reps: 8,
            rpe: 7,
            completed: true,
          ),
        ),
      );
    }).toList();
  }

  /// See `MockTodayRepository`'s own doc comment for why this delay is
  /// deliberate, not decorative — it lets loading states actually be
  /// observed. `short: true` is used for logging actions, which the UX/UI
  /// Design Bible describes as needing to feel immediate (Section 5.2:
  /// "the dominant control... optimistic, immediate").
  Future<void> _delay({bool short = false}) {
    return Future<void>.delayed(Duration(milliseconds: short ? 80 : 300));
  }
}
