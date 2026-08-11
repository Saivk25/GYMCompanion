import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/network.dart';
import '../../../design/design.dart';
import '../application/auth_controller.dart';
import '../domain/auth_models.dart';

/// The Register screen — reached only from [LoginScreen]'s own "Create
/// one" action (`lib/features/auth/presentation/login_screen.dart`),
/// never from the router's initial location. See that file's own doc
/// comment for why this is the one licensed new feature screen this
/// phase adds, and for the same "no explicit navigation on success"
/// reasoning: a successful registration moves [authControllerProvider]
/// to [AuthAuthenticated], which the router's own reactive redirect
/// already handles.
///
/// [RecordReadinessRequest]-style backend requirements aside, `POST
/// /register` needs two fields this screen does not show the user a
/// picker for: `locale` and `timezone`
/// (`backend/app/api/schemas/auth.py`'s `RegisterRequest`). `locale` is
/// read from the real device locale (`Localizations.localeOf(context)`,
/// converted to a BCP-47 tag via `Locale.toLanguageTag()` — no new
/// dependency). `timezone` has no equivalent zero-dependency source in
/// Flutter (there is no built-in IANA timezone name resolver, unlike
/// locale); this screen sends the fixed value `'UTC'`, a real, valid
/// IANA zone name the backend's own `Timezone` value object accepts
/// (`backend/app/domain/user/value_objects.py`, validated against
/// `zoneinfo`) — a disclosed simplification, not a fabricated
/// capability, and a real candidate for a small follow-up phase (a
/// `timezone`-package addition) rather than something to guess a richer
/// answer for here.
class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final TextEditingController _email = TextEditingController();
  final TextEditingController _password = TextEditingController();
  final TextEditingController _confirmPassword = TextEditingController();
  String? _localValidationError;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    _confirmPassword.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_password.text != _confirmPassword.text) {
      setState(() => _localValidationError = 'Passwords do not match.');
      return;
    }
    setState(() => _localValidationError = null);

    final Locale deviceLocale = Localizations.localeOf(context);
    await ref.read(authControllerProvider.notifier).register(
          email: _email.text.trim(),
          password: _password.text,
          locale: deviceLocale.toLanguageTag(),
          // See this file's own doc comment for why 'UTC' — a real,
          // valid IANA zone, not a fabricated one — is used here.
          timezone: 'UTC',
        );
  }

  @override
  Widget build(BuildContext context) {
    final AsyncValue<AuthState> authState = ref.watch(authControllerProvider);
    final bool isSubmitting = authState.isLoading;
    final String? errorMessage =
        _localValidationError ?? (authState.hasError ? _messageFor(authState.error) : null);

    return Scaffold(
      appBar: AppBar(title: const Text('Create account')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              if (errorMessage != null) ...<Widget>[
                _RegisterErrorCard(message: errorMessage),
                const SizedBox(height: AppSpacing.md),
              ],
              AppTextField(
                label: 'Email',
                controller: _email,
                keyboardType: TextInputType.emailAddress,
                autofillHints: const <String>[AutofillHints.email],
                textInputAction: TextInputAction.next,
              ),
              const SizedBox(height: AppSpacing.md),
              AppTextField(
                label: 'Password',
                controller: _password,
                obscureText: true,
                autofillHints: const <String>[AutofillHints.newPassword],
                textInputAction: TextInputAction.next,
              ),
              const SizedBox(height: AppSpacing.md),
              AppTextField(
                label: 'Confirm password',
                controller: _confirmPassword,
                obscureText: true,
                autofillHints: const <String>[AutofillHints.newPassword],
                textInputAction: TextInputAction.done,
                onSubmitted: (_) => _submit(),
              ),
              const SizedBox(height: AppSpacing.lg),
              AppButton(
                label: 'Create account',
                isLoading: isSubmitting,
                onPressed: isSubmitting ? null : _submit,
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// `RegisterHandler`'s one documented failure mode maps to a real 400
  /// (`backend/app/api/errors.py`: "email already registered" is an
  /// ordinary caller-correctable validation failure) — its real
  /// `detail` string is shown unchanged, since (unlike Login) there is
  /// no security reason to obscure *why* registration failed.
  String _messageFor(Object? error) {
    if (error is ApiException) {
      return error.message;
    }
    return 'Something went wrong. Please try again.';
  }
}

class _RegisterErrorCard extends StatelessWidget {
  const _RegisterErrorCard({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    return AppCard(
      child: Row(
        children: <Widget>[
          Icon(AppIcons.warning, color: colorScheme.error, size: 20),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Text(message, style: TextStyle(color: colorScheme.error)),
          ),
        ],
      ),
    );
  }
}
