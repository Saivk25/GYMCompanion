# ADR 0044: Authentication module — Step 2 of production integration

- Status: accepted
- Date: 2026-08-08

## Context

`docs/adr/0042-production-integration-plan.md`'s Step 2 called for a real
Auth module — login, register, refresh, logout, current user — sitting on
top of Step 1's transport-only `lib/core/network/` (`docs/adr/0043-core-
networking-layer.md`), and for the app's first real session guard. Every
one of this app's five tabs, plus Readiness, has run since its own phase
against a mock repository with no login screen in front of it at all
(ADR 0041's own closing line: "No authentication flow exists yet."). This
phase closes that gap, and — per the driving directive's own "Backend
remains the single source of truth" ground rule — against the real,
already-verified backend contracts (`POST /register`/`/login`/`/refresh`/
`/logout`, `GET /me`), not a guessed shape.

## Decision

**`lib/features/auth/` follows the exact four-layer pattern every other
feature already uses** (`domain/` → `application/` → `infrastructure/` →
`presentation/`), including a repository interface
(`AuthRepository`) an `ApiAuthRepository` implements and a
`MockAuthRepository` exists purely for tests — never wired in
`main.dart`. The one deliberate deviation from that pattern: Auth's mock
was never the *production* implementation the way `MockTodayRepository`
etc. still are today. `ApiAuthRepository`'s own doc comment states this
directly — Auth had no "mock until the real backend arrives" era to
begin with, because the real backend already existed when this module
was built. `main.dart` wires `authRepositoryProvider` to
`ApiAuthRepository` unconditionally.

**`AuthController extends AsyncNotifier<AuthState>`**, a three-state
sealed class (`AuthInitial`/`AuthAuthenticated(user)`/
`AuthUnauthenticated`) layered under Riverpod's own loading/error/data
states — `authState.isLoading` and `authState.hasError` still work
exactly as every other controller's caller already expects, and
`AuthState` itself only needs to answer "logged in, as whom, or not."
`build()` does the cold-start dance once, on its own: read a stored
refresh token, attempt a real refresh, fetch `/me`, and resolve to
`AuthAuthenticated`; any failure at any of those steps resolves to
`AuthUnauthenticated` instead of leaving the app in a stuck `AsyncError`
a user could never dismiss — a cold start with a dead refresh token is
an expected, ordinary case (the token expired, was revoked, or the user
reinstalled the app), not an error state a screen should ever render.

**The access token lives in memory only; the refresh token is the one
thing persisted, and only in `flutter_secure_storage`** (Keychain/
Keystore-backed, not `shared_preferences`) — never in a Riverpod state
object a widget could log or a hot-reload could serialize. `TokenStorage`
is its own interface (`SecureTokenStorage` real, `MockTokenStorage` for
tests) for the same reason `AuthRepository` is: the composition root
(`main.dart`) is the only place that ever sees the real implementation.

**`ApiClient` gained one method (`postEmpty`) during this phase**, not a
redesign of Step 1: `POST /logout` returns 204 No Content, and every
existing `ApiClient.post` assumed a JSON body to decode. This is the one
change to an already-committed Step 1 file this phase makes, and it is
purely additive — no existing method's signature or behavior changed.

**`AuthController` is the one closure-based bridge between
`lib/core/network/` and `lib/features/auth/`**, wired at the composition
root exactly as ADR 0043 anticipated: `main.dart`'s new
`apiClientProvider` passes `accessTokenProvider`/`refreshToken`/
`onRefreshFailed` closures that read `authControllerProvider.notifier`.
`ApiAuthRepository` itself is built on that same shared client, opting
out of the default bearer-header/refresh-retry behavior per call via
`skipAuthHeader`/`skipAuthRetry` (login/register/refresh must never
attach a not-yet-issued access token or trigger a refresh loop on their
own 401s).

**The router becomes a `Provider<GoRouter>`, not a bare top-level
constant — the one architecture change this phase makes, and a licensed
one.** `go_router`'s `redirect` callback is synchronous and has no
built-in way to react to an asynchronous Riverpod state change on its
own; the standard, documented bridge is a `ChangeNotifier` that
`ref.listen`s the relevant provider and calls `notifyListeners()`, passed
as `refreshListenable`. Building that bridge requires `ref` at
construction time, which a bare top-level `GoRouter` constant never had.
This is exactly the kind of "real blocker" the driving directive's own
"do not redesign the architecture unless a real blocker is discovered"
clause anticipated — every route table, every existing route, and every
screen's own navigation code is unchanged; only the router's own
construction site moved from a top-level constant into a `Provider`.

**A `/splash` route, not a redirect flash.** Without it, the ~1-2 second
window while `AuthController.build()` resolves a stored refresh token
would either flash `/today`'s real content before redirecting to
`/login`, or flash `/login` before redirecting to `/today` — both wrong.
`_authRedirect` sends `authAsync.isLoading` straight to `/splash`
instead, and `initialLocation` now points there.

**Logout is reached from the existing Settings icon, not a new sixth
tab or new screen** — `docs/TECH_DEBT.md`'s TD-0003 already named
"Settings has an obvious real destination once any account/profile
screen exists" as its own trigger condition; a real confirmation dialog
(`showAppConfirmationDialog`, already used elsewhere) plus real sign-out
is that destination, without fabricating a full account/profile screen
this phase has no scope for.

**`register_screen.dart` sends a fixed `timezone: 'UTC'`** — a real,
valid IANA zone the backend's own `Timezone` value object accepts, not a
guessed or fabricated one — because Flutter has no built-in IANA
timezone-name resolver the way it has a device locale
(`Localizations.localeOf(context)`). This is disclosed in the file's own
doc comment as a real, later-scoped gap (a `timezone`-package addition),
not silently guessed at.

**`AppTextField` gained `obscureText`/`autofillHints`/`textInputAction`/
`onSubmitted`, converting it from `StatelessWidget` to
`StatefulWidget`**, rather than either screen bypassing it with a bare
`TextField` — the project's standing "extend the design system first"
rule. Verified backward-compatible: the one pre-existing call site uses
only already-existing named parameters. `AppIcons` gained
`showPassword`/`hidePassword` for the obscure-text toggle, the same
closed-token pattern every other icon in this app already follows.

## Consequences

**Every pre-existing widget test that pumps `GymCompanionApp` needed an
auth-state override.** 12 files, 23 override blocks, now spread a shared
`authenticatedTestOverrides()` helper (`test/support/
auth_test_overrides.dart`) into their `overrides:` list — the guard
evaluates on the very first frame, so an unauthenticated default would
redirect every existing test to `/login` before its own target screen
ever rendered. This mirrors the same structural reason Coach's own
`coachRepositoryProvider` override became mandatory in every test (ADR
0041), and is a shared helper (not 23 copy-pasted lines) because this
pair needs two providers plus one piece of shared reasoning, not one.

**No feature repository changed.** `lib/features/{today,train,fuel,
progress,readiness,coach}/` are all still on their existing mocks —
Step 3 (per-feature repository integration, one feature at a time,
starting with Today) is the next, separately-scoped phase.

**Not yet verified by execution** — same disclosed constraint as every
prior phase (ADR 0002, restated in ADR 0043): no Flutter/Dart SDK exists
in this sandbox. This phase's test suite (`auth_controller_test.dart` —
11 tests over `AuthController`'s full lifecycle at the `ProviderContainer`
level; `auth_flow_test.dart` — 7 widget tests through the real
`GymCompanionApp`/router covering signed-out/signed-in boot, a real
login and registration submit, password-mismatch validation, and
logout) is structurally verified (brace/paren/bracket balance,
`print()`/cross-feature-import/bare-`Icons.*` sweeps) but has not been
executed.
