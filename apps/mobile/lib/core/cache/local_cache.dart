import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// The one local persistence mechanism every real `ApiXRepository`'s own
/// read-through cache (`read_through_cache.dart`) is built on — Step 4
/// of `docs/adr/0042-production-integration-plan.md`, recorded in full
/// in `docs/adr/0052-offline-caching.md`. A thin wrapper around
/// `SharedPreferences`, not a bespoke cache per feature — see that ADR's
/// own trade-off record for why `shared_preferences` was chosen over
/// Hive/Drift/sqflite for this app's actual cache shape: a handful of
/// small JSON view-state blobs, read and written by key, with no
/// querying or relational needs.
///
/// Every entry is stored as one JSON string envelope —
/// `{"cachedAt": "<iso8601>", "data": <raw>}` — under a key namespaced
/// with [_keyPrefix], so this cache can coexist with any other future
/// use of the same `SharedPreferences` instance without a key collision.
class LocalCache {
  const LocalCache(this._prefs);

  final SharedPreferences _prefs;

  static const String _keyPrefix = 'gym_companion_cache::';

  /// Synchronous, like every `SharedPreferences` read once the instance
  /// itself has resolved (`main.dart` awaits `SharedPreferences
  /// .getInstance()` once, before this app's first frame) — callers
  /// never need to `await` a cache read, which is what makes the
  /// immediate "peek" `readThroughCache` (`read_through_cache.dart`)
  /// performs on its stale-while-revalidate path possible without an
  /// extra async hop.
  CacheEntry? read(String key) {
    final String? raw = _prefs.getString('$_keyPrefix$key');
    if (raw == null) return null;
    final Map<String, dynamic> envelope = jsonDecode(raw) as Map<String, dynamic>;
    return CacheEntry(
      data: envelope['data'],
      cachedAt: DateTime.parse(envelope['cachedAt'] as String),
    );
  }

  /// [cachedAt] is normally omitted, defaulting to the real write
  /// moment — every production call site (`read_through_cache.dart`)
  /// does exactly that. It exists as a parameter at all so a test can
  /// seed a deliberately stale entry (a [cachedAt] far enough in the
  /// past to exceed whatever `maxAge` it wants to exercise) through this
  /// same public method, rather than needing to know this class's own
  /// private on-disk key format just to backdate one value.
  Future<void> write(String key, Object? data, {DateTime? cachedAt}) async {
    final String envelope = jsonEncode(<String, dynamic>{
      'cachedAt': (cachedAt ?? DateTime.now()).toIso8601String(),
      'data': data,
    });
    await _prefs.setString('$_keyPrefix$key', envelope);
  }

  /// Removes exactly one entry, so the next read for [key] is a cold-cache
  /// miss and `readThroughCache` (`read_through_cache.dart`) is forced onto
  /// its live-fetch path rather than its stale-while-revalidate fast path.
  ///
  /// The one call site every mutation-then-refetch repository method uses
  /// (`ApiReadinessRepository.submitCheckIn`, `ApiFuelRepository.logMeal`/
  /// `.logWater`, `ApiProgressRepository.logMeasurement`): each of those
  /// controllers (`ReadinessHomeController`/`FuelHomeController`/
  /// `ProgressHomeController`) calls `fetchHome()` again immediately after
  /// a successful write, on the existing, already-tested "mutate → refetch
  /// shows the new entry immediately" contract those controllers'
  /// own doc comments describe. Without this call, a `fetchHome()` within
  /// [kCacheFreshDuration] of the *previous* read would take the
  /// stale-while-revalidate fast path and silently return the pre-mutation
  /// cached list — a real regression this phase's own caching layer would
  /// otherwise introduce into behavior that already worked and was already
  /// tested before Step 4. See `docs/adr/0052`'s own "cache invalidation on
  /// mutation" section for the full reasoning, including why this is
  /// deliberately narrower than a `forceRefresh` bypass on pull-to-refresh
  /// (a disclosed, different trade-off — see that ADR).
  Future<void> invalidate(String key) => _prefs.remove('$_keyPrefix$key');

  /// Called once, from `AuthController._clearLocalSession`
  /// (`features/auth/application/auth_controller.dart`) — every cached
  /// entry is per-account data (a user's own workouts, meals,
  /// measurements, check-ins), so a logout must not leave it behind for
  /// the next person to sign into this device and see on their very
  /// first, still-loading frame. See `docs/adr/0052`'s own reasoning for
  /// why this is a full clear on logout rather than a per-user key
  /// namespace carried through every repository constructor.
  Future<void> clearAll() async {
    final Iterable<String> keys = _prefs.getKeys().where((String k) => k.startsWith(_keyPrefix));
    await Future.wait(keys.map(_prefs.remove));
  }
}

/// One cached value plus when it was written — [cachedAt] is what
/// [isStale] and every offline/stale-while-revalidate decision in
/// `read_through_cache.dart` is based on.
class CacheEntry {
  const CacheEntry({required this.data, required this.cachedAt});

  /// The raw, already-decoded JSON this entry was written with —
  /// whatever shape the caller's own `fetchRawJson` closure returned
  /// (`read_through_cache.dart`), never a domain object. See that file's
  /// own doc comment for why caching raw JSON, not a parsed view state,
  /// is the deliberate design here.
  final Object? data;

  final DateTime cachedAt;

  bool isStale(Duration maxAge) => DateTime.now().difference(cachedAt) > maxAge;
}

/// A shared freshness window for every feature's stale-while-revalidate
/// policy — one constant, not five different per-feature tunings, since
/// nothing about this app's actual data (a workout plan, a check-in
/// history, a logged meal) argues for treating one feature's staleness
/// tolerance differently from another's until real usage data says
/// otherwise.
const Duration kCacheFreshDuration = Duration(minutes: 5);

/// No default — overridden once, in `main.dart`, after `main()` awaits
/// `SharedPreferences.getInstance()` (which is itself async and cannot
/// resolve inside a synchronous `Provider` body). Every other provider
/// in this app that wraps a plugin instance (`apiClientProvider`'s
/// `Dio`) follows the same "resolve the real instance once at startup,
/// read it via `ref` from then on" shape.
final Provider<SharedPreferences> sharedPreferencesProvider = Provider<SharedPreferences>(
  (ref) => throw UnimplementedError(
    'sharedPreferencesProvider has no default implementation — see '
    'lib/main.dart, which overrides it with the real SharedPreferences '
    'instance resolved before runApp.',
  ),
);

final Provider<LocalCache> localCacheProvider =
    Provider<LocalCache>((ref) => LocalCache(ref.read(sharedPreferencesProvider)));
