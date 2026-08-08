/// Barrel export for `lib/core/mapping/` — import this, not the
/// individual files, from any DTO. Mirrors `core/network/network.dart`'s
/// own barrel convention.
///
/// `lib/core/mapping/` is [core/network/]'s sibling, not a layer on top
/// of it: `core/network/` maps *transport* — HTTP/`dio` failures into
/// one `ApiException` shape (`ApiErrorMapper`). `core/mapping/` maps a
/// *successful* response's already-decoded JSON into this app's own
/// DTOs and, from there, into domain models. Two distinct concerns,
/// cleanly separated — see `docs/adr/0045-shared-api-mapping-
/// convention.md` for the full convention both are part of.
library;

export 'api_date_time.dart';
export 'json_field.dart';
