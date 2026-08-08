/// Small, typed helpers for pulling fields out of a decoded JSON object
/// (`Map<String, dynamic>` — exactly what `ApiClient.get`/`getList`
/// already decode every response into; see `core/network/api_client.dart`).
/// Every `ApiXRepository`'s DTOs use these instead of ad hoc
/// `json['x'] as T` casts scattered through each mapping site, so a
/// malformed or drifted backend response fails in one place, with one
/// clear message, not as a cryptic `type 'Null' is not a subtype of type
/// 'String'` deep inside a `fromJson` constructor with no field name
/// attached to the error at all.
///
/// A field that fails to extract here is *always* a contract-drift bug
/// (the backend's own response shape disagrees with what this DTO
/// expects) or a genuine backend defect — never a normal, expected
/// runtime condition the way a 404 or a validation error is.
/// `ApiErrorMapper` (`core/network/api_error_mapper.dart`) exists for
/// the latter, transport-level failures; this file is not a second
/// error-mapping layer stacked on top of it — it exists only to make
/// the former fail loudly and specifically, pointing at exactly which
/// field and which JSON object, instead of failing crypticly.
///
/// See `docs/adr/0045-shared-api-mapping-convention.md` for the full
/// DTO/mapping convention this file is one piece of.
library;

extension JsonFieldExtraction on Map<String, dynamic> {
  T _require<T>(String key) {
    final Object? value = this[key];
    if (value == null) {
      throw FormatException('Missing required field "$key" in JSON object: $this');
    }
    if (value is! T) {
      throw FormatException(
        'Field "$key" was ${value.runtimeType}, expected $T, in JSON object: $this',
      );
    }
    return value;
  }

  /// A required `str` field.
  String requireString(String key) => _require<String>(key);

  /// A required `bool` field.
  bool requireBool(String key) => _require<bool>(key);

  /// A required numeric field, read as `int` — accepts either a JSON
  /// integer or a JSON float with no fractional part (`json`'s own
  /// number type does not distinguish them the way Dart's `int`/`double`
  /// do), matching every backend integer field this app's DTOs read
  /// (`sleep_quality`, `set_number`, ...).
  int requireInt(String key) => _require<num>(key).toInt();

  /// A required numeric field, read as `double` — every backend `float`
  /// field (`weight`, `resting_heart_rate`, ...).
  double requireDouble(String key) => _require<num>(key).toDouble();

  /// A required JSON array — element-level parsing (e.g. mapping each
  /// entry through a nested DTO's own `fromJson`) is the caller's job;
  /// this only asserts the field itself is present and is a list.
  List<dynamic> requireList(String key) => _require<List<dynamic>>(key);

  /// A required JSON object (nested `Map<String, dynamic>`).
  Map<String, dynamic> requireObject(String key) => _require<Map<String, dynamic>>(key);

  /// An optional `str | null` field — `null` (missing or explicit JSON
  /// `null`) means exactly what the backend's own schema already
  /// documents it to mean for that field; this helper never invents a
  /// default.
  String? optionalString(String key) => this[key] as String?;

  bool? optionalBool(String key) => this[key] as bool?;

  int? optionalInt(String key) => (this[key] as num?)?.toInt();

  double? optionalDouble(String key) => (this[key] as num?)?.toDouble();

  List<dynamic>? optionalList(String key) => this[key] as List<dynamic>?;
}
