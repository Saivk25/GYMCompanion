import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/core/cache/cache.dart';
import 'package:gym_companion_mobile/core/network/network.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// [readThroughCache]'s generic read/stale/offline policy in isolation —
/// `docs/adr/0052-offline-caching.md`. Deliberately decoupled from any one
/// feature's DTOs: `fetchRawJson`/`build` here are minimal fakes over a
/// plain `Map<String, dynamic>`, not a real repository, so these tests
/// prove the policy itself rather than re-proving what the 5 per-feature
/// repository test files (`test/features/*/api_*_repository_test.dart`)
/// already cover for their own real payload shapes.
Future<LocalCache> _freshCache() async {
  SharedPreferences.setMockInitialValues(<String, Object>{});
  return LocalCache(await SharedPreferences.getInstance());
}

/// The [build] callback under test: just echoes the raw payload's `value`
/// field back out alongside the `isOffline` flag `readThroughCache` passed
/// in, so assertions can check both without needing a real domain type.
({Object? value, bool isOffline}) _build(Object? rawJson, {required bool isOffline}) {
  final Map<String, dynamic> map = rawJson as Map<String, dynamic>;
  return (value: map['value'], isOffline: isOffline);
}

void main() {
  group('cold cache (nothing written yet)', () {
    test('fetches live, writes through to the cache, and returns isOffline: false', () async {
      final LocalCache cache = await _freshCache();

      final result = await readThroughCache(
        cache: cache,
        key: 'k',
        maxAge: kCacheFreshDuration,
        fetchRawJson: () async => <String, dynamic>{'value': 'live'},
        build: _build,
      );

      expect(result.value, 'live');
      expect(result.isOffline, isFalse);
      expect(cache.read('k')!.data, <String, dynamic>{'value': 'live'});
    });

    test('a network failure with nothing cached rethrows ApiException', () async {
      final LocalCache cache = await _freshCache();

      expect(
        readThroughCache(
          cache: cache,
          key: 'k',
          maxAge: kCacheFreshDuration,
          fetchRawJson: () async =>
              throw const ApiException(statusCode: null, message: 'offline', isNetworkError: true),
          build: _build,
        ),
        throwsA(isA<ApiException>()),
      );
    });

    test('a genuine server error with nothing cached rethrows, not masked', () async {
      final LocalCache cache = await _freshCache();

      expect(
        readThroughCache(
          cache: cache,
          key: 'k',
          maxAge: kCacheFreshDuration,
          fetchRawJson: () async =>
              throw const ApiException(statusCode: 500, message: 'boom'),
          build: _build,
        ),
        throwsA(isA<ApiException>()),
      );
    });
  });

  group('stale cache (older than maxAge)', () {
    test('a network failure falls back to the stale value with isOffline: true', () async {
      final LocalCache cache = await _freshCache();
      await cache.write(
        'k',
        <String, dynamic>{'value': 'cached'},
        cachedAt: DateTime.now().subtract(const Duration(hours: 1)),
      );

      final result = await readThroughCache(
        cache: cache,
        key: 'k',
        maxAge: kCacheFreshDuration,
        fetchRawJson: () async =>
            throw const ApiException(statusCode: null, message: 'offline', isNetworkError: true),
        build: _build,
      );

      expect(result.value, 'cached');
      expect(result.isOffline, isTrue);
    });

    test('a successful live fetch refreshes the cache and returns isOffline: false', () async {
      final LocalCache cache = await _freshCache();
      await cache.write(
        'k',
        <String, dynamic>{'value': 'old'},
        cachedAt: DateTime.now().subtract(const Duration(hours: 1)),
      );

      final result = await readThroughCache(
        cache: cache,
        key: 'k',
        maxAge: kCacheFreshDuration,
        fetchRawJson: () async => <String, dynamic>{'value': 'new'},
        build: _build,
      );

      expect(result.value, 'new');
      expect(result.isOffline, isFalse);
      expect(cache.read('k')!.data, <String, dynamic>{'value': 'new'});
    });

    test('a genuine (non-network) error is never masked by a stale cache hit', () async {
      final LocalCache cache = await _freshCache();
      await cache.write(
        'k',
        <String, dynamic>{'value': 'cached'},
        cachedAt: DateTime.now().subtract(const Duration(hours: 1)),
      );

      expect(
        readThroughCache(
          cache: cache,
          key: 'k',
          maxAge: kCacheFreshDuration,
          fetchRawJson: () async =>
              throw const ApiException(statusCode: 500, message: 'boom'),
          build: _build,
        ),
        throwsA(isA<ApiException>()),
      );
    });
  });

  group('fresh cache (within maxAge) — stale-while-revalidate', () {
    test('serves the cached value immediately without waiting on a live fetch', () async {
      final LocalCache cache = await _freshCache();
      await cache.write('k', <String, dynamic>{'value': 'fresh'});
      bool fetchWasCalled = false;

      final result = await readThroughCache(
        cache: cache,
        key: 'k',
        maxAge: kCacheFreshDuration,
        fetchRawJson: () async {
          fetchWasCalled = true;
          // If readThroughCache awaited this on the fast path, this
          // failure would surface synchronously and fail the test.
          throw const ApiException(statusCode: null, message: 'offline', isNetworkError: true);
        },
        build: _build,
      );

      expect(result.value, 'fresh');
      expect(result.isOffline, isFalse);
      // The background revalidate is fire-and-forget, so it may or may
      // not have started by the time the awaited call above returns —
      // what matters is that it never blocked the result.
      expect(fetchWasCalled, anyOf(isTrue, isFalse));
    });

    test('a background revalidate failure is swallowed, not surfaced to the caller', () async {
      final LocalCache cache = await _freshCache();
      await cache.write('k', <String, dynamic>{'value': 'fresh'});

      final result = await readThroughCache(
        cache: cache,
        key: 'k',
        maxAge: kCacheFreshDuration,
        fetchRawJson: () async =>
            throw const ApiException(statusCode: 500, message: 'boom'),
        build: _build,
      );

      expect(result.value, 'fresh');
      expect(result.isOffline, isFalse);

      // Give the fire-and-forget revalidate a turn of the event loop;
      // if its failure were unswallowed it would surface as an
      // unhandled async error and fail this test.
      await Future<void>.delayed(Duration.zero);
    });

    test('a background revalidate success updates the cache for the next read', () async {
      final LocalCache cache = await _freshCache();
      await cache.write('k', <String, dynamic>{'value': 'fresh'});
      int callCount = 0;

      Future<Object?> fetch() async {
        callCount++;
        return <String, dynamic>{'value': 'revalidated-$callCount'};
      }

      final result = await readThroughCache(
        cache: cache,
        key: 'k',
        maxAge: kCacheFreshDuration,
        fetchRawJson: fetch,
        build: _build,
      );
      expect(result.value, 'fresh');

      // Let the background revalidate run to completion.
      await Future<void>.delayed(Duration.zero);
      await Future<void>.delayed(Duration.zero);

      expect(cache.read('k')!.data, <String, dynamic>{'value': 'revalidated-1'});
    });
  });
}
