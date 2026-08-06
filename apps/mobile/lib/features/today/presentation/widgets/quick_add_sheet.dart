import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../design/design.dart';

/// The Today tab's single FAB opens exactly this sheet (UX/UI Design
/// Bible Section 4: "One FAB, scoped to the Today tab only (Quick Add:
/// meal, water, note)"). Presented via `showAppBottomSheet` from
/// `AppShell`, per that helper's own bottom-sheet chrome — see
/// `AppShell`'s doc comment for why the FAB itself lives in the shell
/// rather than in `TodayScreen`.
///
/// "Log a meal" is real navigation (Fuel already exists as a tab, even
/// mid-build). Water and Note have no destination yet — dedicated
/// quick-entry flows for either are not part of any screen built so far
/// — so they surface the same honest "not built yet" signal
/// `TodayScreen`'s own deferred actions use, rather than silently doing
/// nothing.
class QuickAddSheet extends StatelessWidget {
  const QuickAddSheet({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        // This extra AppSpacing.lg is deliberate, not doubled-up by
        // accident: showAppBottomSheet already insets its content by
        // AppSpacing.lg, and AppListTile below adds its own
        // AppSpacing.lg internal padding on top of that — so without
        // this wrapper, "Quick add" would sit 16px from the sheet edge
        // while every row's title sits 32px in, visibly misaligned.
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
          child: Text('Quick add', style: Theme.of(context).textTheme.titleLarge),
        ),
        const SizedBox(height: AppSpacing.sm),
        AppListTile(
          leadingIcon: AppIcons.fuel,
          title: 'Log a meal',
          onTap: () {
            Navigator.of(context).pop();
            context.go('/fuel');
          },
        ),
        AppListTile(
          leadingIcon: AppIcons.add,
          title: 'Log water',
          onTap: () {
            Navigator.of(context).pop();
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Water logging is not built yet.')),
            );
          },
        ),
        AppListTile(
          leadingIcon: AppIcons.edit,
          title: 'Add a note',
          onTap: () {
            Navigator.of(context).pop();
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Notes are not built yet.')),
            );
          },
        ),
      ],
    );
  }
}
