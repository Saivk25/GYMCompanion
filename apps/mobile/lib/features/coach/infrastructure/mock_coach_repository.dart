import '../../../shared/domain/coach_signal.dart';
import '../application/coach_controller.dart';

/// The real [CoachRepository] implementation this app runs today — see
/// that interface's own doc comment for why "real" and "mock" are not
/// opposites here the way they are for every other module. [signalsReader]
/// is a plain callback rather than a `Ref`, so this class stays pure
/// Dart with no Riverpod import of its own, matching every other mock
/// repository's own shape; `lib/main.dart` supplies
/// `() => ref.read(coachSignalLogProvider)` when constructing this class,
/// which is the one place this module's composition actually touches
/// Riverpod internals directly.
///
/// Deliberately holds no state of its own (unlike `MockReadinessRepository`/
/// `MockFuelRepository`/`MockTrainRepository`, which each own an
/// in-memory `List<...>`): the real, single source of truth is the
/// shared `CoachSignalLog` every producing module's own controller
/// writes into; duplicating that list here would risk exactly the kind
/// of silent-drift bug this codebase's own "never recreate backend logic"
/// discipline exists to prevent, applied here to not recreating *this
/// client's own* shared state a second time.
class MockCoachRepository implements CoachRepository {
  const MockCoachRepository(this._signalsReader);

  final List<CoachSignal> Function() _signalsReader;

  @override
  Future<List<CoachSignal>> fetchRecentSignals() async {
    await _delay();
    return _signalsReader();
  }

  /// See `MockTodayRepository`'s own doc comment for why this delay is
  /// deliberate, not decorative — kept short since this "fetch" does no
  /// real I/O, only enough to make Coach Home's loading skeleton
  /// genuinely observable in a manual test pass.
  Future<void> _delay() => Future<void>.delayed(const Duration(milliseconds: 120));
}
