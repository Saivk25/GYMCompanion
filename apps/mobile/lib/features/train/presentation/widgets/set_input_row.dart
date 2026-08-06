import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../../design/design.dart';

/// The dominant control on the Active Workout screen (UX/UI Design Bible
/// Section 5.2: the set-log input is "the dominant control... optimistic,
/// immediate"). Three compact [AppTextField]s (weight/reps/RPE) plus one
/// [AppButton] — real, functioning numeric entry, not a placeholder,
/// since this is the single most-used control in the entire Train
/// module.
class SetInputRow extends StatefulWidget {
  const SetInputRow({
    required this.setNumber,
    required this.onLog,
    this.suggestedWeight,
    this.suggestedReps,
    super.key,
  });

  final int setNumber;
  final double? suggestedWeight;
  final int? suggestedReps;
  final void Function({required double weight, required int reps, required int rpe}) onLog;

  @override
  State<SetInputRow> createState() => _SetInputRowState();
}

class _SetInputRowState extends State<SetInputRow> {
  late final TextEditingController _weightController;
  late final TextEditingController _repsController;
  late final TextEditingController _rpeController;

  @override
  void initState() {
    super.initState();
    _weightController = TextEditingController(
      text: widget.suggestedWeight?.toStringAsFixed(0) ?? '',
    );
    _repsController = TextEditingController(text: widget.suggestedReps?.toString() ?? '');
    _rpeController = TextEditingController();
  }

  @override
  void dispose() {
    _weightController.dispose();
    _repsController.dispose();
    _rpeController.dispose();
    super.dispose();
  }

  bool get _isValid {
    final double? weight = double.tryParse(_weightController.text);
    final int? reps = int.tryParse(_repsController.text);
    final int? rpe = int.tryParse(_rpeController.text);
    return weight != null && weight > 0 && reps != null && reps > 0 && rpe != null && rpe >= 1 && rpe <= 10;
  }

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        Text(
          'Set ${widget.setNumber}',
          style: textTheme.labelMedium?.copyWith(color: colorScheme.onSurfaceVariant),
        ),
        const SizedBox(height: AppSpacing.xs),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Expanded(
              child: AppTextField(
                label: 'Weight',
                controller: _weightController,
                dense: true,
                textAlign: TextAlign.center,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                inputFormatters: <TextInputFormatter>[
                  FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d*')),
                ],
                onChanged: (_) => setState(() {}),
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: AppTextField(
                label: 'Reps',
                controller: _repsController,
                dense: true,
                textAlign: TextAlign.center,
                keyboardType: TextInputType.number,
                inputFormatters: <TextInputFormatter>[FilteringTextInputFormatter.digitsOnly],
                onChanged: (_) => setState(() {}),
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: AppTextField(
                label: 'RPE',
                controller: _rpeController,
                dense: true,
                textAlign: TextAlign.center,
                keyboardType: TextInputType.number,
                inputFormatters: <TextInputFormatter>[FilteringTextInputFormatter.digitsOnly],
                onChanged: (_) => setState(() {}),
              ),
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.sm),
        AppButton(
          label: 'Log set',
          fullWidth: false,
          onPressed: _isValid
              ? () => widget.onLog(
                    weight: double.parse(_weightController.text),
                    reps: int.parse(_repsController.text),
                    rpe: int.parse(_rpeController.text),
                  )
              : null,
        ),
      ],
    );
  }
}
