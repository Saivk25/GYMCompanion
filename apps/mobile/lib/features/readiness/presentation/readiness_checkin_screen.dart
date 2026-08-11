import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../design/design.dart';
import '../application/readiness_controller.dart';
import '../domain/readiness_models.dart';

/// The Readiness Check-in flow — UX/UI Design Bible Section 5.4:
/// "Capture the daily sleep/stress/soreness/pain/GI snapshot in under
/// ten seconds... The five input controls only, pre-filled to
/// yesterday's values as a low-friction default to adjust rather than
/// re-enter." One screen, matching the Bible's own single-screen spec
/// exactly — not six separate screens for Sleep/Energy/Stress/Soreness/
/// RHR/HRV, which the Bible never asks for and this module's own
/// directive not to invent screens rules out. `pain_flags`/`GI_symptoms`
/// are not modeled anywhere in the backend
/// (`docs/adr/0040-readiness-module.md`) — they route through a
/// `SafetyFlag` aggregate this codebase hasn't built — so this screen's
/// six real inputs (sleep duration + quality, energy, stress, soreness,
/// resting heart rate, heart rate variability) are exactly
/// `RecordReadinessRequest`'s own fields, no more, no less.
///
/// [AppRatingSlider] is used for the four bounded 1-10 self-report
/// fields; free physiological numbers (sleep hours, resting heart rate,
/// HRV) use the same [AppTextField] decimal-entry pattern
/// `LogMeasurementScreen` already established.
class ReadinessCheckInScreen extends ConsumerStatefulWidget {
  const ReadinessCheckInScreen({super.key});

  @override
  ConsumerState<ReadinessCheckInScreen> createState() => _ReadinessCheckInScreenState();
}

class _ReadinessCheckInScreenState extends ConsumerState<ReadinessCheckInScreen> {
  bool _prefilled = false;
  bool _isSubmitting = false;

  final TextEditingController _sleepHours = TextEditingController();
  int _sleepQuality = 5;
  int _energy = 5;
  int _stress = 5;
  int _soreness = 5;
  final TextEditingController _restingHr = TextEditingController();
  final TextEditingController _hrv = TextEditingController();
  final TextEditingController _notes = TextEditingController();

  /// Bible: "pre-filled to yesterday's values as a low-friction default
  /// to adjust rather than re-enter." Runs once, the first time real
  /// data is available — mutating these fields directly (not via
  /// `setState`) is safe here because it happens before this same
  /// `build()` call constructs the widgets that read them; no frame has
  /// painted with the un-prefilled values yet.
  void _prefillFrom(ReadinessEntry? latest) {
    if (_prefilled) return;
    _prefilled = true;
    if (latest == null) return;
    if (latest.sleepDuration != null) {
      _sleepHours.text = (latest.sleepDuration!.inMinutes / 60).toStringAsFixed(1);
    }
    _sleepQuality = latest.sleepQuality ?? _sleepQuality;
    _energy = latest.energyLevel ?? _energy;
    _stress = latest.stressLevel ?? _stress;
    _soreness = latest.sorenessLevel ?? _soreness;
    if (latest.restingHeartRate != null) {
      _restingHr.text = latest.restingHeartRate!.toStringAsFixed(0);
    }
    if (latest.heartRateVariability != null) {
      _hrv.text = latest.heartRateVariability!.toStringAsFixed(0);
    }
  }

  @override
  void dispose() {
    _sleepHours.dispose();
    _restingHr.dispose();
    _hrv.dispose();
    _notes.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() => _isSubmitting = true);
    try {
      final double? sleepHoursValue = double.tryParse(_sleepHours.text);
      await ref.read(readinessHomeControllerProvider.notifier).submitCheckIn(
            date: DateTime.now(),
            sleepDuration: sleepHoursValue != null
                ? Duration(minutes: (sleepHoursValue * 60).round())
                : null,
            sleepQuality: _sleepQuality,
            energyLevel: _energy,
            stressLevel: _stress,
            sorenessLevel: _soreness,
            restingHeartRate: double.tryParse(_restingHr.text),
            heartRateVariability: double.tryParse(_hrv.text),
            notes: _notes.text,
          );
      if (!mounted) return;
      // Bible: "A brief confirmation transition back to Today, not a
      // separate 'thank you' screen." Pops straight back to whichever
      // screen launched this flow (Today's check-in nudge or Readiness
      // Home) — the destination already re-renders with the fresh
      // state, including any real advisory warnings this submission
      // returned.
      Navigator.of(context).pop();
    } catch (_) {
      if (!mounted) return;
      setState(() => _isSubmitting = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Couldn't submit this check-in. Try again.")),
      );
    }
  }

  List<TextInputFormatter> get _decimalFormatters => <TextInputFormatter>[
        FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d*')),
      ];

  @override
  Widget build(BuildContext context) {
    final AsyncValue<ReadinessHomeViewState> state = ref.watch(readinessHomeControllerProvider);
    final ReadinessHomeViewState? loaded = state.valueOrNull;
    if (loaded != null) {
      _prefillFrom(loaded.entries.isEmpty ? null : loaded.entries.first);
    }

    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(AppIcons.back),
          tooltip: 'Back',
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Readiness check-in'),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          children: <Widget>[
            Text(
              'A few quick questions set today\'s session tier.',
              style: textTheme.bodyMedium?.copyWith(color: colorScheme.onSurfaceVariant),
            ),
            const SizedBox(height: AppSpacing.xl),
            Text('Sleep', style: textTheme.titleMedium),
            const SizedBox(height: AppSpacing.sm),
            AppTextField(
              label: 'Hours',
              controller: _sleepHours,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              inputFormatters: _decimalFormatters,
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: AppSpacing.lg),
            AppRatingSlider(
              label: 'Sleep quality',
              value: _sleepQuality,
              onChanged: (int v) => setState(() => _sleepQuality = v),
            ),
            const SizedBox(height: AppSpacing.xl),
            AppRatingSlider(
              label: 'Energy',
              value: _energy,
              onChanged: (int v) => setState(() => _energy = v),
            ),
            const SizedBox(height: AppSpacing.lg),
            AppRatingSlider(
              label: 'Stress',
              value: _stress,
              onChanged: (int v) => setState(() => _stress = v),
            ),
            const SizedBox(height: AppSpacing.lg),
            AppRatingSlider(
              label: 'Soreness',
              value: _soreness,
              onChanged: (int v) => setState(() => _soreness = v),
            ),
            const SizedBox(height: AppSpacing.xl),
            Text('Recovery metrics (optional)', style: textTheme.titleMedium),
            const SizedBox(height: AppSpacing.sm),
            Row(
              children: <Widget>[
                Expanded(
                  child: AppTextField(
                    label: 'Resting HR (bpm)',
                    controller: _restingHr,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: _decimalFormatters,
                    textInputAction: TextInputAction.next,
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: AppTextField(
                    label: 'HRV (ms)',
                    controller: _hrv,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: _decimalFormatters,
                    textInputAction: TextInputAction.next,
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.lg),
            AppTextField(
              label: 'Notes (optional)',
              controller: _notes,
              textInputAction: TextInputAction.done,
              onSubmitted: (_) => FocusScope.of(context).unfocus(),
            ),
            const SizedBox(height: AppSpacing.xxl),
            AppButton(
              label: 'Submit check-in',
              isLoading: _isSubmitting,
              onPressed: _isSubmitting ? null : _submit,
            ),
          ],
        ),
      ),
    );
  }
}
