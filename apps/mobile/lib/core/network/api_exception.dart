/// The one exception type that ever crosses out of `lib/core/network/`
/// — every real repository implementation catches [DioException]
/// (`package:dio`) internally and rethrows this instead, so no
/// controller or widget anywhere in this app ever needs to know Dio
/// exists. Per `docs/adr/0042-production-integration-plan.md` Part 2's
/// "unified error mapping" decision: one exception type, one status-code
/// switch, because the real backend's own failure surface
/// (`backend/app/api/errors.py`) is already exactly this small and
/// fully enumerated — 400, 401, 403, 404, 422, 500, plus a genuine
/// network failure with no status code at all.
class ApiException implements Exception {
  const ApiException({
    required this.statusCode,
    required this.message,
    this.isNetworkError = false,
  });

  /// The real backend HTTP status code, when a response was received at
  /// all. `null` exactly when [isNetworkError] is `true` — a timeout, a
  /// dropped connection, or no connectivity at all never produced a
  /// status code to report, so `null` here is a real, meaningful
  /// "the server was never reached," not a missing-data placeholder.
  final int? statusCode;

  /// Sourced directly from the backend's own `ErrorResponse.detail`
  /// (`backend/app/api/schemas/common.py`) wherever a response body
  /// existed — never a client-invented message standing in for a real
  /// backend explanation. Only the network-failure branch (no response
  /// body to source a message from) uses a client-authored string, and
  /// that string names the network condition itself, not a guess at
  /// what the backend would have said.
  final String message;

  final bool isNetworkError;

  bool get isUnauthorized => statusCode == 401;
  bool get isForbidden => statusCode == 403;
  bool get isNotFound => statusCode == 404;
  bool get isValidationError => statusCode == 422;
  bool get isBadRequest => statusCode == 400;
  bool get isServerError => statusCode != null && statusCode! >= 500;

  @override
  String toString() =>
      'ApiException(statusCode: $statusCode, isNetworkError: $isNetworkError, message: $message)';
}
