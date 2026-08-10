import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/core/cache/local_cache.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// [LocalCache] against a real (mocked) [SharedPreferences] instance —
/// `docs/adr/0052-offline-caching.md`. Not against a hand-rolled fake:
/// [LocalCache] is a thin concrete wrapper, not an interface, so
/// proving it against the real plugin (in its standard test-mode
/// in-memory backing) is what actually verifies the on-disk envelope
/// shape, not just that this file agrees with itself.
Future<LocalCache> _freshCache() async {
  SharedPreferences.setMockInitialValues(<String, Object>{});
  return LocalCache(await SharedPreferences.getInstance());
}

void main() {
  test('a key that was never written reads as null', () async {
    final LocalCache cache = await _freshCache();

    expect(cache.read('missing'), isNull);
  });

  test('write then read round-trips the exact data, with a real cachedAt', () async {
    final LocalCache cache = await _freshCache();
    final DateTime before = DateTime.now();

    await cache.write('today', <String, dynamic>{'a': 1, 'b': <int>[1, 2, 3]});

    final CacheEntry? entry = cache.read('today');
    expect(entry, isNotNull);
    expect(entry!.data, <String, dynamic>{'a': 1, 'b': <int>[1, 2, 3]});
    expect(entry.cachedAt.isAfter(before.subtract(const Duration(seconds: 1))), isTrue);
    expect(entry.cachedAt.isBefore(DateTime.now().add(const Duration(seconds: 1))), isTrue);
  });

  test('write accepts an explicit cachedAt, for seeding a deliberately stale entry', () async {
    final LocalCache cache = await _freshCache();
    final DateTime old = DateTime.now().subtract(const Duration(days: 1));

    await cache.write('today', <String, dynamic>{'x': true}, cachedAt: old);

    final CacheEntry entry = cache.read('today')!;
    expect(entry.cachedAt, old);
  });

  test('isStale is false within maxAge and true beyond it', () async {
    final CacheEntry fresh = CacheEntry(data: null, cachedAt: DateTime.now());
    final CacheEntry old = CacheEntry(
      data: null,
      cachedAt: DateTime.now().subtract(const Duration(minutes: 10)),
    );

    expect(fresh.isStale(const Duration(minutes: 5)), isFalse);
    expect(old.isStale(const Duration(minutes: 5)), isTrue);
  });

  test('different keys do not collide', () async {
    final LocalCache cache = await _freshCache();

    await cache.write('today', <String, dynamic>{'feature': 'today'});
    await cache.write('fuel_home', <String, dynamic>{'feature': 'fuel'});

    expect(cache.read('today')!.data, <String, dynamic>{'feature': 'today'});
    expect(cache.read('fuel_home')!.data, <String, dynamic>{'feature': 'fuel'});
  });

  test('clearAll removes every cache entry this class wrote', () async {
    final LocalCache cache = await _freshCache();
    await cache.write('today', <String, dynamic>{'a': 1});
    await cache.write('fuel_home', <String, dynamic>{'b': 2});

    await cache.clearAll();

    expect(cache.read('today'), isNull);
    expect(cache.read('fuel_home'), isNull);
  });

  test('invalidate removes only the named key, leaving others intact', () async {
    final LocalCache cache = await _freshCache();
    await cache.write('today', <String, dynamic>{'a': 1});
    await cache.write('fuel_home', <String, dynamic>{'b': 2});

    await cache.invalidate('today');

    expect(cache.read('today'), isNull);
    expect(cache.read('fuel_home')!.data, <String, dynamic>{'b': 2});
  });

  test('invalidate on a key that was never written is a harmless no-op', () async {
    final LocalCache cache = await _freshCache();

    await cache.invalidate('missing');

    expect(cache.read('missing'), isNull);
  });

  test('clearAll does not touch unrelated SharedPreferences keys', () async {
    SharedPreferences.setMockInitialValues(<String, Object>{'someone_elses_key': 'keep-me'});
    final SharedPreferences prefs = await SharedPreferences.getInstance();
    final LocalCache cache = LocalCache(prefs);
    await cache.write('today', <String, dynamic>{'a': 1});

    await cache.clearAll();

    expect(prefs.getString('someone_elses_key'), 'keep-me');
  });
}
