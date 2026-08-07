import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../design/design.dart';
import '../../application/fuel_controller.dart';

/// Hydration quick-log (UX/UI Design Bible Section 5.11: "Fast water
/// logging… Log an amount"). A bottom sheet, not a full screen — the
/// same fast-entry pattern `QuickAddSheet` already established for
/// Today's own quick-add row, chosen for the same reason: this is
/// explicitly meant to be quick, and a full-screen drill-in would work
/// against that.
///
/// Quick-amount chips cover the common case in one tap; the custom field
/// exists for everything else. Both paths call the same
/// [FuelHomeController.logWater] — a quick-amount tap is not a shortcut
/// around real logging, it is real logging with the amount pre-filled.
class WaterLogSheet extends ConsumerStatefulWidget {
  const WaterLogSheet({super.key});

  @override
  ConsumerState<WaterLogSheet> createState() => _WaterLogSheetState();
}

class _WaterLogSheetState extends ConsumerState<WaterLogSheet> {
  final TextEditingController _amount = TextEditingController();
  bool _isSubmitting = false;

  static const List<double> _quickAmounts = <double>[250, 500, 750];

  @override
  void dispose() {
    _amount.dispose();
    super.dispose();
  }

  Future<void> _log(double amountMl) async {
    setState(() => _isSubmitting = true);
    try {
      await ref
          .read(fuelHomeControllerProvider.notifier)
          .logWater(date: DateTime.now(), amountMl: amountMl);
      if (!mounted) return;
      Navigator.of(context).pop();
    } catch (_) {
      if (!mounted) return;
      setState(() => _isSubmitting = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Couldn't log water. Try again.")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final double? customAmount = double.tryParse(_amount.text);

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
          child: Text('Log water', style: textTheme.titleLarge),
        ),
        const SizedBox(height: AppSpacing.lg),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
          child: Wrap(
            spacing: AppSpacing.sm,
            children: <Widget>[
              for (final double amount in _quickAmounts)
                AppButton(
                  label: '${amount.round()} ml',
                  variant: AppButtonVariant.secondary,
                  fullWidth: false,
                  isLoading: _isSubmitting,
                  onPressed: _isSubmitting ? null : () => _log(amount),
                ),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.xl),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Expanded(
                child: AppTextField(
                  label: 'Custom amount (ml)',
                  controller: _amount,
                  keyboardType: TextInputType.number,
                  inputFormatters: <TextInputFormatter>[FilteringTextInputFormatter.digitsOnly],
                  onChanged: (_) => setState(() {}),
                ),
              ),
              const SizedBox(width: AppSpacing.sm),
              AppButton(
                label: 'Log',
                fullWidth: false,
                isLoading: _isSubmitting,
                onPressed: (customAmount != null && customAmount > 0 && !_isSubmitting)
                    ? () => _log(customAmount)
                    : null,
              ),
            ],
          ),
        ),
      ],
    );
  }
}
