import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';

/// A minimal, hand-written [HttpClientAdapter] fake — no mock-HTTP
/// package dependency added just for tests. [responses] is consumed
/// strictly in order, one per call to [fetch]; a script that runs out
/// of scripted responses throws, so an over-eager retry (or a missing
/// scripted response) fails the test loudly rather than hanging.
class FakeHttpClientAdapter implements HttpClientAdapter {
  FakeHttpClientAdapter(this.responses) : responder = null;

  /// An alternate construction mode for scripts that depend on *which*
  /// call this is rather than strict list order — e.g. a concurrency
  /// test where two requests race and either could be "the first" one
  /// the fake adapter actually receives.
  FakeHttpClientAdapter.responding(this.responder) : responses = const <FakeResponse>[];

  final List<FakeResponse> responses;
  final FakeResponse Function(RequestOptions options, int callIndex)? responder;
  final List<RequestOptions> requests = <RequestOptions>[];
  int _cursor = 0;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    final int callIndex = requests.length;
    requests.add(options);

    final FakeResponse next;
    if (responder != null) {
      next = responder!(options, callIndex);
    } else {
      if (_cursor >= responses.length) {
        throw StateError(
          'FakeHttpClientAdapter ran out of scripted responses '
          '(${requests.length} requests made, only ${responses.length} scripted).',
        );
      }
      next = responses[_cursor];
      _cursor++;
    }

    if (next.throwConnectionError) {
      throw DioException(
        requestOptions: options,
        type: DioExceptionType.connectionError,
        message: 'fake connection error',
      );
    }

    final String body = next.body == null ? '' : jsonEncode(next.body);
    return ResponseBody.fromString(
      body,
      next.statusCode,
      headers: <String, List<String>>{
        Headers.contentTypeHeader: <String>['application/json'],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

class FakeResponse {
  const FakeResponse({
    this.statusCode = 200,
    this.body,
    this.throwConnectionError = false,
  });

  final int statusCode;
  final Object? body;
  final bool throwConnectionError;
}
