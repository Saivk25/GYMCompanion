import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/core/network/api_client.dart';
import 'package:gym_companion_mobile/core/network/api_exception.dart';

import 'fakes/fake_http_client_adapter.dart';

ApiClient _clientWith(FakeHttpClientAdapter adapter) {
  final Dio dio = Dio(BaseOptions(baseUrl: 'http://test'));
  dio.httpClientAdapter = adapter;
  return ApiClient(dio: dio);
}

void main() {
  group('ApiClient success paths', () {
    test('get() returns the decoded JSON object', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(body: <String, dynamic>{'id': 'g1', 'name': 'Lose fat'}),
      ]);
      final ApiClient client = _clientWith(adapter);

      final Map<String, dynamic> result = await client.get('/api/v1/goals/g1');

      expect(result, <String, dynamic>{'id': 'g1', 'name': 'Lose fat'});
    });

    test('getList() returns the decoded JSON array, not unwrapped further', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(
          body: <Map<String, dynamic>>[
            <String, dynamic>{'id': 'g1'},
            <String, dynamic>{'id': 'g2'},
          ],
        ),
      ]);
      final ApiClient client = _clientWith(adapter);

      final List<dynamic> result = await client.getList('/api/v1/goals');

      expect(result, hasLength(2));
    });

    test('post() sends the real IdResponse{id, warnings} shape through unchanged', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(
          statusCode: 201,
          body: <String, dynamic>{
            'id': 'n1',
            'warnings': <String>['[advisory] logged close to your calorie target'],
          },
        ),
      ]);
      final ApiClient client = _clientWith(adapter);

      final Map<String, dynamic> result = await client.post(
        '/api/v1/nutrition',
        body: <String, dynamic>{'calories': 500},
      );

      expect(result['id'], 'n1');
      expect(result['warnings'], <String>['[advisory] logged close to your calorie target']);
    });
  });

  group('ApiClient error mapping', () {
    test('a 404 with a real ErrorResponse body throws ApiException, not DioException', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(statusCode: 404, body: <String, dynamic>{'detail': 'goal not found'}),
      ]);
      final ApiClient client = _clientWith(adapter);

      await expectLater(
        client.get('/api/v1/goals/missing'),
        throwsA(
          isA<ApiException>()
              .having((e) => e.statusCode, 'statusCode', 404)
              .having((e) => e.message, 'message', 'goal not found'),
        ),
      );
    });
  });

  group('ApiClient retry policy (docs/adr/0042 Part 2)', () {
    test('a GET retries once on a connection error and succeeds on the second attempt', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(throwConnectionError: true),
        const FakeResponse(body: <String, dynamic>{'status': 'ok'}),
      ]);
      final ApiClient client = _clientWith(adapter);

      final Map<String, dynamic> result = await client.get('/health');

      expect(result, <String, dynamic>{'status': 'ok'});
      expect(adapter.requests, hasLength(2));
    });

    test('a GET gives up and throws a network ApiException after maxRetries is exhausted', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(throwConnectionError: true),
        const FakeResponse(throwConnectionError: true),
        const FakeResponse(throwConnectionError: true),
      ]);
      final ApiClient client = _clientWith(adapter);

      await expectLater(
        client.get('/health'),
        throwsA(isA<ApiException>().having((e) => e.isNetworkError, 'isNetworkError', isTrue)),
      );
      // ApiConfig.maxRetries == 2, so exactly 3 attempts total (1 original + 2 retries).
      expect(adapter.requests, hasLength(3));
    });

    test('a POST never auto-retries on a connection error — see RetryInterceptor\'s own doc '
        'comment on why a mutation is unsafe to retry blindly against this backend', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(throwConnectionError: true),
      ]);
      final ApiClient client = _clientWith(adapter);

      await expectLater(
        client.post('/api/v1/nutrition', body: <String, dynamic>{'calories': 500}),
        throwsA(isA<ApiException>()),
      );
      expect(adapter.requests, hasLength(1));
    });
  });
}
