/// The three states every screen in this app needs a consistent answer
/// for, per the UX/UI Design Bible: empty ("Silence is a valid state...
/// not an error to hide"), loading ("Skeleton screens matching the final
/// layout... never a spinner" for anything predictable), and error
/// ("Clear and calm, always paired with a retry action; never just a red
/// X with no next step").
library;

import 'package:flutter/material.dart';

import '../tokens/tokens.dart';
import 'app_button.dart';

/// A calm, centered placeholder for a screen or section with nothing to
/// show yet — a new user, a not-yet-started history, a below-threshold
/// data view. Never framed as an error: [icon] and [message] should read
/// as a normal, expected state, matching the Bible's "silence is a valid
/// state" principle.
class AppEmptyState extends StatelessWidget {
  const AppEmptyState({
    required this.icon,
    required this.title,
    this.message,
    this.actionLabel,
    this.onAction,
    super.key,
  });

  final IconData icon;
  final String title;
  final String? message;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final TextTheme textTheme = Theme.of(context).textTheme;

    return Padding(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.xxxl,
        vertical: AppSpacing.massive,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(icon, size: 40, color: colorScheme.onSurfaceVariant),
          const SizedBox(height: AppSpacing.lg),
          Text(
            title,
            textAlign: TextAlign.center,
            style: textTheme.titleLarge,
          ),
          if (message != null) ...<Widget>[
            const SizedBox(height: AppSpacing.sm),
            Text(
              message!,
              textAlign: TextAlign.center,
              style: textTheme.bodyMedium,
            ),
          ],
          if (actionLabel != null) ...<Widget>[
            const SizedBox(height: AppSpacing.xl),
            AppButton(
              label: actionLabel!,
              onPressed: onAction,
              variant: AppButtonVariant.secondary,
              expand: false,
            ),
          ],
        ],
      ),
    );
  }
}

/// A calm, specific error message, always paired with a retry action —
/// per the Bible, this app never shows "just a red X with no next step."
class AppErrorState extends StatelessWidget {
  const AppErrorState({
    required this.message,
    required this.onRetry,
    this.retryLabel = 'Try again',
    super.key,
  });

  final String message;
  final VoidCallback onRetry;
  final String retryLabel;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final TextTheme textTheme = Theme.of(context).textTheme;

    return Padding(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.xxxl,
        vertical: AppSpacing.massive,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(AppIcons.warning, size: 40, color: colorScheme.onSurfaceVariant),
          const SizedBox(height: AppSpacing.lg),
          Text(
            message,
            textAlign: TextAlign.center,
            style: textTheme.bodyMedium,
          ),
          const SizedBox(height: AppSpacing.xl),
          AppButton(
            label: retryLabel,
            onPressed: onRetry,
            icon: AppIcons.retry,
            variant: AppButtonVariant.secondary,
            expand: false,
          ),
        ],
      ),
    );
  }
}

/// A rounded placeholder block for a skeleton loading layout — compose
/// several of these, shaped and sized to match the final content's real
/// layout, rather than showing a spinner. A gentle, slow opacity pulse
/// (not a shimmer sweep — a sweep is a decorative flourish this system's
/// motion guidelines reject) signals "loading" without drawing more
/// attention than the layout it stands in for; the pulse respects the OS
/// reduced-motion setting via [AppMotion.resolve].
class AppSkeletonBox extends StatefulWidget {
  const AppSkeletonBox({
    required this.width,
    required this.height,
    this.radius = AppRadius.radiusSm,
    super.key,
  });

  final double width;
  final double height;
  final BorderRadius radius;

  @override
  State<AppSkeletonBox> createState() => _AppSkeletonBoxState();
}

class _AppSkeletonBoxState extends State<AppSkeletonBox>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final Duration duration = AppMotion.resolve(
      context,
      const Duration(milliseconds: 900),
    );

    if (duration == Duration.zero) {
      return DecoratedBox(
        decoration: BoxDecoration(
          color: colorScheme.surfaceContainerHighest,
          borderRadius: widget.radius,
        ),
        child: SizedBox(width: widget.width, height: widget.height),
      );
    }

    return AnimatedBuilder(
      animation: _controller,
      builder: (BuildContext context, Widget? child) {
        final double opacity = 0.6 + (_controller.value * 0.3);
        return Opacity(
          opacity: opacity,
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: colorScheme.surfaceContainerHighest,
              borderRadius: widget.radius,
            ),
            child: SizedBox(width: widget.width, height: widget.height),
          ),
        );
      },
    );
  }
}

/// A short, genuinely indeterminate wait only — per the Bible, "spinners
/// reserved only for short, genuinely indeterminate waits" (e.g. the
/// Coach's typing indicator while a model call is in flight). Any
/// predictable-shape loading state should use [AppSkeletonBox] instead.
class AppLoadingIndicator extends StatelessWidget {
  const AppLoadingIndicator({this.size = 20, super.key});

  final double size;

  @override
  Widget build(BuildContext context) {
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    return SizedBox(
      width: size,
      height: size,
      child: CircularProgressIndicator(
        strokeWidth: 2,
        valueColor: AlwaysStoppedAnimation<Color>(colorScheme.primary),
      ),
    );
  }
}
