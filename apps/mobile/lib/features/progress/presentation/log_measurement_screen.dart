import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../design/design.dart';
import '../application/progress_controller.dart';

/// Log measurements — UX/UI Design Bible's "Measurement entry" (Section
/// 5.11 catalog) and the "Measurements" user flow (Section 6.7): "Enters
/// weight/waist/hip/etc. -> Saved as an append-only record." Real: maps
/// to `POST /api/v1/progress` (`RecordProgressRequest`) with whichever
/// fields the user filled in populated. Fields are grouped exactly the
/// way the backend's own two update endpoints group them
/// (`PUT .../body-composition`, `PUT .../measurements`) — a client
/// mirroring the backend's own boundary, not inventing a different one.
class LogMeasurementScreen extends ConsumerStatefulWidget {
  const LogMeasurementScreen({super.key});

  @override
  ConsumerState<LogMeasurementScreen> createState() => _LogMeasurementScreenState();
}

class _LogMeasurementScreenState extends ConsumerState<LogMeasurementScreen> {
  bool _isSubmitting = false;

  final TextEditingController _weight = TextEditingController();
  final TextEditingController _bodyFat = TextEditingController();
  final TextEditingController _leanMass = TextEditingController();
  final TextEditingController _muscleMass = TextEditingController();
  final TextEditingController _waist = TextEditingController();
  final TextEditingController _chest = TextEditingController();
  final TextEditingController _hip = TextEditingController();
  final TextEditingController _arm = TextEditingController();
  final TextEditingController _thigh = TextEditingController();
  final TextEditingController _calf = TextEditingController();
  final TextEditingController _neck = TextEditingController();
  final TextEditingController _notes = TextEditingController();

  late final List<TextEditingController> _numericControllers = <TextEditingController>[
    _weight, _bodyFat, _leanMass, _muscleMass,
    _waist, _chest, _hip, _arm, _thigh, _calf, _neck,
  ];

  @override
  void dispose() {
    for (final TextEditingController controller in _numericControllers) {
      controller.dispose();
    }
    _notes.dispose();
    super.dispose();
  }

  bool get _canSubmit => _numericControllers.any((TextEditingController c) => double.tryParse(c.text) != null);

  Future<void> _submit() async {
    setState(() => _isSubmitting = true);
    try {
      await ref.read(progressHomeControllerProvider.notifier).logMeasurement(
            date: DateTime.now(),
            bodyWeight: double.tryParse(_weight.text),
            bodyFatPercentage: double.tryParse(_bodyFat.text),
            leanBodyMass: double.tryParse(_leanMass.text),
            muscleMass: double.tryParse(_muscleMass.text),
            waist: double.tryParse(_waist.text),
            chest: double.tryParse(_chest.text),
            hip: double.tryParse(_hip.text),
            arm: double.tryParse(_arm.text),
            thigh: double.tryParse(_thigh.text),
            calf: double.tryParse(_calf.text),
            neck: double.tryParse(_neck.text),
            notes: _notes.text,
          );
      if (!mounted) return;
      Navigator.of(context).pop();
    } catch (_) {
      if (!mounted) return;
      setState(() => _isSubmitting = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Couldn't log this check-in. Try again.")),
      );
    }
  }

  List<TextInputFormatter> get _decimalFormatters => <TextInputFormatter>[
        FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d*')),
      ];

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(AppIcons.back),
          tooltip: 'Back',
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Log measurements'),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          children: <Widget>[
            Text('Body composition', style: textTheme.titleMedium),
            const SizedBox(height: AppSpacing.sm),
            Row(
              children: <Widget>[
                Expanded(
                  child: AppTextField(
                    label: 'Weight (kg)',
                    controller: _weight,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: _decimalFormatters,
                    textInputAction: TextInputAction.next,
                    onChanged: (_) => setState(() {}),
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: AppTextField(
                    label: 'Body fat (%)',
                    controller: _bodyFat,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: _decimalFormatters,
                    textInputAction: TextInputAction.next,
                    onChanged: (_) => setState(() {}),
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.sm),
            Row(
              children: <Widget>[
                Expanded(
                  child: AppTextField(
                    label: 'Lean mass (kg)',
                    controller: _leanMass,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: _decimalFormatters,
                    textInputAction: TextInputAction.next,
                    onChanged: (_) => setState(() {}),
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: AppTextField(
                    label: 'Muscle mass (kg)',
                    controller: _muscleMass,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: _decimalFormatters,
                    textInputAction: TextInputAction.next,
                    onChanged: (_) => setState(() {}),
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.xl),
            Text('Measurements (cm)', style: textTheme.titleMedium),
            const SizedBox(height: AppSpacing.sm),
            Row(
              children: <Widget>[
                Expanded(
                  child: AppTextField(
                    label: 'Waist',
                    controller: _waist,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: _decimalFormatters,
                    textInputAction: TextInputAction.next,
                    onChanged: (_) => setState(() {}),
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: AppTextField(
                    label: 'Chest',
                    controller: _chest,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: _decimalFormatters,
                    textInputAction: TextInputAction.next,
                    onChanged: (_) => setState(() {}),
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.sm),
            Row(
              children: <Widget>[
                Expanded(
                  child: AppTextField(
                    label: 'Hip',
                    controller: _hip,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: _decimalFormatters,
                    textInputAction: TextInputAction.next,
                    onChanged: (_) => setState(() {}),
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: AppTextField(
                    label: 'Arm',
                    controller: _arm,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: _decimalFormatters,
                    textInputAction: TextInputAction.next,
                    onChanged: (_) => setState(() {}),
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.sm),
            Row(
              children: <Widget>[
                Expanded(
                  child: AppTextField(
                    label: 'Thigh',
                    controller: _thigh,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: _decimalFormatters,
                    textInputAction: TextInputAction.next,
                    onChanged: (_) => setState(() {}),
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: AppTextField(
                    label: 'Calf',
                    controller: _calf,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: _decimalFormatters,
                    textInputAction: TextInputAction.next,
                    onChanged: (_) => setState(() {}),
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.sm),
            AppTextField(
              label: 'Neck',
              controller: _neck,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              inputFormatters: _decimalFormatters,
              textInputAction: TextInputAction.next,
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: AppSpacing.lg),
            AppTextField(
              label: 'Notes (optional)',
              controller: _notes,
              textInputAction: TextInputAction.done,
              onSubmitted: (_) => FocusScope.of(context).unfocus(),
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              'Fill in whatever you have — nothing here is required, and each '
              'check-in is saved as its own record, never overwriting the last.',
              style: textTheme.bodySmall?.copyWith(color: colorScheme.onSurfaceVariant),
            ),
            const SizedBox(height: AppSpacing.xxl),
            AppButton(
              label: 'Log check-in',
              isLoading: _isSubmitting,
              onPressed: _canSubmit ? _submit : null,
            ),
          ],
        ),
      ),
    );
  }
}
