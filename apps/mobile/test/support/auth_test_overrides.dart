import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:gym_companion_mobile/features/auth/application/auth_controller.dart';
import 'package:gym_companion_mobile/features/auth/infrastructure/mock_auth_repository.dart';

/// The one pair of overrides every widget test that boots the full
/// `GymCompanionApp` needs, so `GoRouter`'s auth guard
/// (`lib/shell/app_router.dart`'s `redirect`) resolves to an
/// already-authenticated session on the very first frame instead of
/// redirecting to `/login` before the test's own target screen ever
/// renders.
///
/// Shared as one function, not copy-pasted per file — unlike ADR 0041's
/// Coach-phase precedent (which repeated a single override line across
/// 10 files because that override was already a one-liner), this pair
/// is two providers plus the reasoning for why both are needed
/// together (see `MockAuthRepository`'s own doc comment), which is
/// exactly the kind of thing that should have one home, not 23 copies
/// across every affected `overrides:` block in this test suite.
///
/// The one deliberate exception is `test/features/auth/` itself, which
/// needs to construct an *unauthenticated* starting state on purpose
/// (to exercise the login/register flow) and so overrides
/// [tokenStorageProvider] with `MockTokenStorage(seedRefreshToken: null)`
/// directly rather than calling this helper.
List<Override> authenticatedTestOverrides() => <Override>[
      authRepositoryProvider.overrideWithValue(const MockAuthRepository()),
      tokenStorageProvider.overrideWithValue(MockTokenStorage()),
    ];
