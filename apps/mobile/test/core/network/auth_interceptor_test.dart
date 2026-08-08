import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/core/network/api_client.dart';
import 'package:gym_companion_mobile/core/network/api_exception.dart';

import 'fakes/fake_http_client_adapter.dart';

void main() {
  group('ApiClient + AuthInterceptor', () {
    test('attaches the real bearer token to an ordinary request', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(body: <String, dynamic>{'ok': true}),
      ]);
      final Dio dio = Dio(BaseOptions(baseUrl: 'http://test'))..httpClientAdapter = adapter;
      final ApiClient client = ApiClient(
        dio: dio,
        accessTokenProvider: () async => 'real-access-token',
      );

      await client.get('/api/v1/goals');

      expect(adapter.requests.single.headers['Authorization'], 'Bearer real-access-token');
    });

    test('skipAuthHeader — used by login/register — sends no Authorization header '
        'even though an access token provider is configured', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(body: <String, dynamic>{'access_token': 'new'}),
      ]);
      final Dio dio = Dio(BaseOptions(baseUrl: 'http://test'))..httpClientAdapter = adapter;
      final ApiClient client = ApiClient(
        dio: dio,
        accessTokenProvider: () async => 'stale-or-irrelevant-token',
      );

      await client.post('/login', body: <String, dynamic>{'email': 'a@b.com'}, skipAuthHeader: true);

      expect(adapter.requests.single.headers.containsKey('Authorization'), isFalse);
    });

    test('a 401 triggers exactly one refresh, then retries the original request '
        'with the new token', () async {
      int refreshCalls = 0;
      String token = 'expired-token';

      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter.responding((options, callIndex) {
        if (callIndex == 0) {
          return const FakeResponse(statusCode: 401, body: <String, dynamic>{'detail': 'expired'});
        }
        return FakeResponse(body: <String, dynamic>{'authHeaderSeen': options.headers['Authorization']});
      });
      final Dio dio = Dio(BaseOptions(baseUrl: 'http://test'))..httpClientAdapter = adapter;
      final ApiClient client = ApiClient(
        dio: dio,
        accessTokenProvider: () async => token,
        refreshToken: () async {
          refreshCalls++;
          token = 'refreshed-token';
          return true;
        },
      );

      final Map<String, dynamic> result = await client.get('/api/v1/goals');

      expect(refreshCalls, 1);
      expect(adapter.requests, hasLength(2));
      expect(result['authHeaderSeen'], 'Bearer refreshed-token');
    });

    test('concurrent 401s during one in-flight refresh trigger exactly one refresh call '
        '(no refresh storm)', () async {
      int refreshCalls = 0;

      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter.responding((options, callIndex) {
        // The first two calls this adapter ever sees are the two
        // original requests racing each other — both 401. Every call
        // after that is a retry, once refresh has resolved.
        if (callIndex < 2) {
          return const FakeResponse(statusCode: 401, body: <String, dynamic>{'detail': 'expired'});
        }
        return const FakeResponse(body: <String, dynamic>{'ok': true});
      });
      final Dio dio = Dio(BaseOptions(baseUrl: 'http://test'))..httpClientAdapter = adapter;
      final ApiClient client = ApiClient(
        dio: dio,
        accessTokenProvider: () async => 'token',
        refreshToken: () async {
          refreshCalls++;
          await Future<void>.delayed(const Duration(milliseconds: 10));
          return true;
        },
      );

      await Future.wait<Map<String, dynamic>>(<Future<Map<String, dynamic>>>[
        client.get('/api/v1/goals'),
        client.get('/api/v1/nutrition'),
      ]);

      expect(refreshCalls, 1);
    });

    test('a failed refresh calls onRefreshFailed once and still surfaces the original 401', () async {
      int onRefreshFailedCalls = 0;

      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(statusCode: 401, body: <String, dynamic>{'detail': 'expired'}),
      ]);
      final Dio dio = Dio(BaseOptions(baseUrl: 'http://test'))..httpClientAdapter = adapter;
      final ApiClient client = ApiClient(
        dio: dio,
        accessTokenProvider: () async => 'expired-token',
        refreshToken: () async => false,
        onRefreshFailed: () async {
          onRefreshFailedCalls++;
        },
      );

      await expectLater(
        client.get('/api/v1/goals'),
        throwsA(isA<ApiException>().having((e) => e.isUnauthorized, 'isUnauthorized', isTrue)),
      );
      expect(onRefreshFailedCalls, 1);
      // No retry attempted — refresh failed, so only the one original request was made.
      expect(adapter.requests, hasLength(1));
    });

    test('skipAuthRetry — used by the refresh call itself — never attempts a refresh loop', () async {
      int refreshCalls = 0;

      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(statusCode: 401, body: <String, dynamic>{'detail': 'refresh token expired'}),
      ]);
      final Dio dio = Dio(BaseOptions(baseUrl: 'http://test'))..httpClientAdapter = adapter;
      final ApiClient client = ApiClient(
        dio: dio,
        accessTokenProvider: () async => null,
        refreshToken: () async {
          refreshCalls++;
          return true;
        },
      );

      await expectLater(
        client.post('/refresh', body: <String, dynamic>{'refresh_token': 'dead'}, skipAuthRetry: true),
        throwsA(isA<ApiException>()),
      );
      expect(refreshCalls, 0);
    });
  });
}
