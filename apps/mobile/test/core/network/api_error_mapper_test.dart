import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/core/network/api_error_mapper.dart';
import 'package:gym_companion_mobile/core/network/api_exception.dart';

RequestOptions _options({String method = 'GET'}) =>
    RequestOptions(path: '/test', method: method);

void main() {
  group('ApiErrorMapper.map', () {
    test('maps a real ErrorResponse{detail: str} body to the same message', () {
      final DioException error = DioException(
        requestOptions: _options(),
        type: DioExceptionType.badResponse,
        response: Response<dynamic>(
          requestOptions: _options(),
          statusCode: 404,
          data: <String, dynamic>{'detail': 'goal not found'},
        ),
      );

      final ApiException result = ApiErrorMapper.map(error);

      expect(result.statusCode, 404);
      expect(result.message, 'goal not found');
      expect(result.isNetworkError, isFalse);
      expect(result.isNotFound, isTrue);
    });

    test('flattens a real ErrorResponse{detail: list[str]} body (422 shape)', () {
      final DioException error = DioException(
        requestOptions: _options(),
        type: DioExceptionType.badResponse,
        response: Response<dynamic>(
          requestOptions: _options(),
          statusCode: 422,
          data: <String, dynamic>{
            'detail': <String>['email: field required', 'password: field required'],
          },
        ),
      );

      final ApiException result = ApiErrorMapper.map(error);

      expect(result.statusCode, 422);
      expect(result.message, 'email: field required; password: field required');
      expect(result.isValidationError, isTrue);
    });

    for (final (int status, bool Function(ApiException) check) in <(int, bool Function(ApiException))>[
      (400, (e) => e.isBadRequest),
      (401, (e) => e.isUnauthorized),
      (403, (e) => e.isForbidden),
      (404, (e) => e.isNotFound),
      (422, (e) => e.isValidationError),
      (500, (e) => e.isServerError),
    ]) {
      test('status $status sets the matching convenience getter', () {
        final DioException error = DioException(
          requestOptions: _options(),
          type: DioExceptionType.badResponse,
          response: Response<dynamic>(
            requestOptions: _options(),
            statusCode: status,
            data: <String, dynamic>{'detail': 'irrelevant'},
          ),
        );

        expect(check(ApiErrorMapper.map(error)), isTrue, reason: 'status $status');
      });
    }

    test('a response with no parseable detail falls back to a generic message', () {
      final DioException error = DioException(
        requestOptions: _options(),
        type: DioExceptionType.badResponse,
        response: Response<dynamic>(
          requestOptions: _options(),
          statusCode: 500,
          data: 'not json',
        ),
      );

      final ApiException result = ApiErrorMapper.map(error);

      expect(result.statusCode, 500);
      expect(result.message, 'Request failed with status 500.');
    });

    for (final DioExceptionType type in <DioExceptionType>[
      DioExceptionType.connectionTimeout,
      DioExceptionType.sendTimeout,
      DioExceptionType.receiveTimeout,
      DioExceptionType.connectionError,
    ]) {
      test('$type maps to isNetworkError with no status code', () {
        final DioException error = DioException(requestOptions: _options(), type: type);

        final ApiException result = ApiErrorMapper.map(error);

        expect(result.isNetworkError, isTrue);
        expect(result.statusCode, isNull);
        expect(result.message, isNotEmpty);
      });
    }

    test('a real backend never needs a client-authored message unless the network failed', () {
      // Documents the contract this mapper is built around: message is
      // only ever client-authored when isNetworkError is true.
      final DioException networkError = DioException(
        requestOptions: _options(),
        type: DioExceptionType.connectionError,
      );
      final DioException backendError = DioException(
        requestOptions: _options(),
        type: DioExceptionType.badResponse,
        response: Response<dynamic>(
          requestOptions: _options(),
          statusCode: 400,
          data: <String, dynamic>{'detail': 'goal name must not be blank'},
        ),
      );

      expect(ApiErrorMapper.map(networkError).isNetworkError, isTrue);
      expect(ApiErrorMapper.map(backendError).isNetworkError, isFalse);
      expect(ApiErrorMapper.map(backendError).message, 'goal name must not be blank');
    });
  });
}
