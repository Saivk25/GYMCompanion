import 'dart:async';

import '../network/network.dart';
import 'local_cache.dart';

/// The one, shared read-through + stale-while-revalidate + offline-
/// fallback policy every real `ApiXRepository`'s own `fetchHome()`/
/// `fetchToday()` reuses — Step 4 of `docs/adr/0042-production-
/// integration-plan.md`, recorded in full in `docs/adr/0052-offline-
/// caching.md`. One generic function, not five hand-rolled per-feature
/// caching mechanisms — the same "one shared layer, not a
/// feature-specific reimplementation" discipline `docs/adr/0045`'s
/// mapping convention already established for DTOs, applied here to
/// caching instead of parsing.
///
/// ## What this caches, and why raw JSON, not the parsed view state
///
/// [fetchRawJson] returns whatever this call's real, already-existing
/// DTO-parsing code needs as its input — the exact same
/// `List<dynamic>`/`Map<String, dynamic>` shape `ApiClient.get`/
/// `.getList` already returns from a live call (or a small
/// `Map<String, dynamic>` bundling more than one such call's raw
/// results, for a `fetchHome()` that issues several parallel `GET`s).
/// Caching the *raw* response, not the constructed view state, means
/// the existing `XxxDto.fromJson`/`.toDomain()` parsing code stays the
/// only place that ever builds a view state — reused unchanged for both
/// a live response and a cached one — rather than requiring a second,
/// hand-written `toJson`/`fromJson` pair on every domain view-state type
/// this project has purely to serialize a cache entry. [build] is that
/// same existing parsing logic, factored into a small function each
/// repository already effectively had inline, called twice: once for a
/// fresh response (`isOffline: false`), once for a cached one
/// (`isOffline` set by whichever branch below actually used it).
///
/// ## Stale-while-revalidate here means the classic HTTP semantic, not a
/// live mid-session UI push
///
/// When a cache entry is younger than [maxAge], it is returned
/// immediately and a real background refetch is kicked off to refresh
/// the cache for the *next* read — the `Cache-Control:
/// stale-while-revalidate` standard's own definition. This call's
/// caller gets the fast, already-known-good answer; the next one gets
/// whatever came back from the network. This does **not** push a
/// second, fresher value into whatever UI is already showing this
/// call's result partway through — doing that would mean every
/// `*HomeController.build()` needing to change shape to accept a second
/// state emission after its `Future` already resolved, which conflicts
/// with this phase's own "keep the existing repository interfaces
/// stable wherever possible" instruction. Disclosed here as a
/// deliberate scope line, not a missed enhancement — see
/// `docs/adr/0052`.
///
/// ## Offline reads
///
/// A real network failure ([ApiException.isNetworkError]) falls back to
/// whatever cache entry exists, however stale, marked via [build]'s own
/// `isOffline: true` — the exact "Offline" state every screen's own
/// `XHomeViewState.isOffline` field has had a slot for since before any
/// real repository existed. A non-network [ApiException] (a real 4xx/5xx
/// from a server that *was* reached) is never masked by a stale cache
/// hit — rethrown unchanged, the same "a real app-level error must not
/// be silently hidden behind old data" posture every prior phase's error
/// handling already took.
Future<T> readThroughCache<T>({
  required LocalCache cache,
  required String key,
  required Duration maxAge,
  required Future<Object?> Function() fetchRawJson,
  required T Function(Object? rawJson, {required bool isOffline}) build,
}) async {
  final CacheEntry? cached = cache.read(key);

  if (cached != null && !cached.isStale(maxAge)) {
    unawaited(_revalidateInBackground(cache: cache, key: key, fetchRawJson: fetchRawJson));
    return build(cached.data, isOffline: false);
  }

  try {
    final Object? fresh = await fetchRawJson();
    await cache.write(key, fresh);
    return build(fresh, isOffline: false);
  } on ApiException catch (error) {
    if (!error.isNetworkError) {
      rethrow;
    }
    if (cached == null) {
      rethrow;
    }
    return build(cached.data, isOffline: true);
  }
}

/// Fire-and-forget cache refresh for the stale-while-revalidate path
/// above — errors are swallowed deliberately: the caller that triggered
/// this already has a perfectly good (if slightly stale) value in hand,
/// and the next call past [maxAge] will simply try the real network
/// again on its own.
Future<void> _revalidateInBackground({
  required LocalCache cache,
  required String key,
  required Future<Object?> Function() fetchRawJson,
}) async {
  try {
    final Object? fresh = await fetchRawJson();
    await cache.write(key, fresh);
  } on Object {
    // Deliberately swallowed — see this function's own doc comment.
  }
}
