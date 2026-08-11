import 'package:flutter/material.dart';

import '../tokens/tokens.dart';

/// A bounded, whole-number subjective rating input (1-10 by default) —
/// this app's answer to the Bible's own "numeric steppers preferred over
/// free text for structured logging" rule (Section 10) for the one shape
/// nothing before Readiness needed: a single bounded scale, not a free
/// numeric quantity ([AppTextField] already covers weight, reps, macros —
/// all unbounded). Built for Readiness's four self-reported check-in
/// fields (sleep quality, energy, stress, soreness), all sharing the
/// backend's own 1-10 bound
/// (`backend/app/domain/readiness/value_objects.py`'s `_MIN/MAX_
/// SUBJECTIVE_RATING`).
///
/// A themed [Slider], not a row of ten tappable numbers — a ten-segment
/// control would either overflow a phone width at accessibility text
/// sizes or force ellipsis on every label, and a slider is the same
/// bounded-rating pattern Apple Health/WHOOP-style check-ins already use.
/// [AppTheme]'s own `sliderTheme` (added this phase) supplies every
/// color; this component decides only the label/value layout and
/// [Semantics] wiring around it.
class AppRatingSlider extends StatelessWidget {
  const AppRatingSlider({
    required this.label,
    required this.value,
    required this.onChanged,
    this.min = 1,
    this.max = 10,
    super.key,
  }) : assert(value >= min && value <= max, 'value must be within [min, max]');

  final String label;

  /// Always a real, in-range number — per the Bible's own "pre-filled to
  /// yesterday's values as a low-friction default to adjust rather than
  /// re-enter" rule (Section 5.4), a caller should seed this from the
  /// most recent real check-in when one exists, never leave it
  /// meaningfully "empty."
  final int value;
  final ValueChanged<int> onChanged;
  final int min;
  final int max;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        Row(
          children: <Widget>[
            Expanded(child: Text(label, style: textTheme.titleMedium)),
            Text(
              '$value',
              style: AppTypography.tabular(
                textTheme.titleMedium?.copyWith(color: colorScheme.onSurfaceVariant) ??
                    const TextStyle(),
              ),
            ),
          ],
        ),
        Slider(
          value: value.toDouble(),
          min: min.toDouble(),
          max: max.toDouble(),
          divisions: max - min,
          label: '$value',
          onChanged: (double v) => onChanged(v.round()),
        ),
      ],
    );
  }
}
