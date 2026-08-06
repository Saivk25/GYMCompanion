import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../tokens/tokens.dart';

/// The one text-input component this app uses. Until this phase, nothing
/// in this design system needed real text entry — every screen so far
/// has been read-only or button-driven. Train's set-logging row (weight/
/// reps/RPE) is the first genuine input requirement, so per this
/// project's own standing rule ("if a required component does not exist,
/// extend the design system first, never bypass it"), this is that
/// extension rather than a bare [TextField] styled inline inside one
/// screen.
///
/// [AppTheme] already defines a complete `inputDecorationTheme` (fill,
/// border, focus, and error colors, all token-driven) — this component
/// does not re-decide any color or border here, only the *label*/
/// *semantics*/*density* behavior every text field in this app should
/// share, the same division of responsibility [AppButton] has with the
/// theme's own button styles.
class AppTextField extends StatelessWidget {
  const AppTextField({
    required this.label,
    this.controller,
    this.hint,
    this.keyboardType,
    this.inputFormatters,
    this.textAlign = TextAlign.start,
    this.dense = false,
    this.errorText,
    this.onChanged,
    super.key,
  });

  final String label;
  final TextEditingController? controller;
  final String? hint;
  final TextInputType? keyboardType;
  final List<TextInputFormatter>? inputFormatters;
  final TextAlign textAlign;

  /// Tighter padding and no floating label gap — used where several
  /// fields sit side by side in a row (Train's weight/reps/RPE set-log
  /// row) and full-size padding would waste the row's limited width.
  final bool dense;

  final String? errorText;
  final ValueChanged<String>? onChanged;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      keyboardType: keyboardType,
      inputFormatters: inputFormatters,
      textAlign: textAlign,
      onChanged: onChanged,
      // A field's accessible name must be its label even when the label
      // is also shown visually as floating text — screen readers read
      // [TextField]'s own `decoration.labelText` correctly already, so
      // no extra [Semantics] wrapper is needed here (unlike [AppButton]'s
      // loading state, which genuinely drops its label from the tree).
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        errorText: errorText,
        isDense: dense,
        contentPadding: dense
            ? const EdgeInsets.symmetric(horizontal: AppSpacing.sm, vertical: AppSpacing.sm)
            : null,
      ),
    );
  }
}
