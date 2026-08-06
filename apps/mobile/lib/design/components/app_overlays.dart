/// Bottom sheet and dialog helpers — the two overlay surfaces this app
/// uses, per the UX/UI Design Bible (Section 10): "Bottom sheets for
/// anything spawned from a tap that needs more input or context — the
/// default mobile pattern throughout. Full-screen dialogs are reserved
/// for truly critical, rare interruptions (Safety Escalation, account
/// deletion)."
///
/// Both helpers route through the ambient [BottomSheetThemeData]/
/// [DialogThemeData] `AppTheme` already registers (drag handle, corner
/// radius, elevation, surface tint) — a screen calling [showAppBottomSheet]
/// never needs to repeat that styling, and cannot accidentally build an
/// overlay that looks different from every other overlay in the app.
library;

import 'package:flutter/material.dart';

import '../tokens/tokens.dart';
import 'app_button.dart';

/// Shows a bottom sheet with this app's standard chrome. [isScrollControlled]
/// should be `true` whenever [builder]'s content can be taller than half
/// the screen (e.g. a form) — the same trade-off `showModalBottomSheet`
/// itself exposes, surfaced here rather than hidden, since getting it
/// wrong either clips content or wastes space.
Future<T?> showAppBottomSheet<T>({
  required BuildContext context,
  required WidgetBuilder builder,
  bool isScrollControlled = false,
}) {
  return showModalBottomSheet<T>(
    context: context,
    isScrollControlled: isScrollControlled,
    builder: (BuildContext sheetContext) {
      return SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(
            AppSpacing.lg,
            AppSpacing.sm,
            AppSpacing.lg,
            AppSpacing.lg,
          ),
          child: builder(sheetContext),
        ),
      );
    },
  );
}

/// Shows the confirmation dialog reserved for genuinely irreversible
/// actions (Bible Section 10: destructive actions "require a second
/// confirmation only when truly irreversible" — everything else uses
/// "undo over confirm" instead of blocking on a dialog at all). Returns
/// `true` if the user confirmed, `false` or `null` otherwise — a caller
/// should treat any non-`true` result as "do not proceed."
Future<bool?> showAppConfirmationDialog({
  required BuildContext context,
  required String title,
  required String message,
  required String confirmLabel,
  String cancelLabel = 'Cancel',
  bool isDestructive = true,
}) {
  return showDialog<bool>(
    context: context,
    builder: (BuildContext dialogContext) {
      return AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: <Widget>[
          AppButton(
            label: cancelLabel,
            variant: AppButtonVariant.tertiary,
            expand: false,
            onPressed: () => Navigator.of(dialogContext).pop(false),
          ),
          AppButton(
            label: confirmLabel,
            variant: isDestructive
                ? AppButtonVariant.destructive
                : AppButtonVariant.primary,
            expand: false,
            onPressed: () => Navigator.of(dialogContext).pop(true),
          ),
        ],
      );
    },
  );
}
