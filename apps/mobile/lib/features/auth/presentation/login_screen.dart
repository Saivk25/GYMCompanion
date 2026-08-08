import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/network/network.dart';
import '../../../design/design.dart';
import '../application/auth_controller.dart';
import '../domain/auth_models.dart';

/// The Login screen — the one genuinely new *feature* screen this
/// production-integration phase adds (every other change in Step 2 is
/// infrastructure). `docs/adr/0042-production-integration-plan.md`
/// itself named this the one real gap its own "do not create new
/// feature screens unless a real gap is discovered" instruction would
/// license: there is no existing screen Login could be folded into, and
/// a real backend to authenticate against is the entire point of this
/// phase.
///
/// No explicit navigation happens in [_submit] — a successful login
/// updates [authControllerProvider]'s state to [AuthAuthenticated],
/// which `lib/shell/app_router.dart`'s reactive `redirect` (via its
/// `GoRouterRefreshNotifier`) already reacts to on its own; this screen
/// only ever calls the controller and lets the router decide where to
/// go next, the same separation every other screen in this app keeps
/// between "call the controller" and "the router owns navigation."
class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final TextEditingController _email = TextEditingController();
  final TextEditingController _password = TextEditingController();

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    await ref.read(authControllerProvider.notifier).login(
          email: _email.text.trim(),
          password: _password.text,
        );
  }

  @override
  Widget build(BuildContext context) {
    final AsyncValue<AuthState> authState = ref.watch(authControllerProvider);
    final bool isSubmitting = authState.isLoading;
    final String? errorMessage = authState.hasError ? _messageFor(authState.error) : null;

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              const SizedBox(height: AppSpacing.xxl),
              Text(
                'Gym Companion',
                style: Theme.of(context).textTheme.headlineMedium,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: AppSpacing.sm),
              Text(
                'Sign in to continue',
                style: Theme.of(context).textTheme.bodyMedium,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: AppSpacing.xl),
              if (errorMessage != null) ...<Widget>[
                _LoginErrorCard(message: errorMessage),
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
                autofillHints: const <String>[AutofillHints.password],
                textInputAction: TextInputAction.done,
                onSubmitted: (_) => _submit(),
              ),
              const SizedBox(height: AppSpacing.lg),
              AppButton(
                label: 'Sign in',
                isLoading: isSubmitting,
                onPressed: isSubmitting ? null : _submit,
              ),
              const SizedBox(height: AppSpacing.md),
              AppButton(
                label: "Don't have an account? Create one",
                variant: AppButtonVariant.tertiary,
                onPressed: isSubmitting ? null : () => context.push('/register'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// `LoginHandler`'s one documented failure mode maps to a real 401
  /// (`backend/app/api/errors.py`: "wrong email or password") — shown
  /// here as a fixed, non-alarming message rather than the raw backend
  /// `detail` string, since a login form should never confirm *which*
  /// of email/password was wrong (a real security consideration the
  /// backend's own error message already avoids by using one message
  /// for both cases). Every other failure (network, validation, server)
  /// surfaces the real backend `detail` unchanged — never fabricated.
  String _messageFor(Object? error) {
    if (error is ApiException) {
      if (error.isUnauthorized) {
        return 'Incorrect email or password.';
      }
      return error.message;
    }
    return 'Something went wrong. Please try again.';
  }
}

class _LoginErrorCard extends StatelessWidget {
  const _LoginErrorCard({required this.message});

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
