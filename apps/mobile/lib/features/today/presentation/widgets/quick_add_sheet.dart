import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../design/design.dart';
import '../../../fuel/presentation/widgets/water_log_sheet.dart';

/// The Today tab's single FAB opens exactly this sheet (UX/UI Design
/// Bible Section 4: "One FAB, scoped to the Today tab only (Quick Add:
/// meal, water, note)"). Presented via `showAppBottomSheet` from
/// `AppShell`, per that helper's own bottom-sheet chrome — see
/// `AppShell`'s doc comment for why the FAB itself lives in the shell
/// rather than in `TodayScreen`.
///
/// "Log a meal" is real navigation to Fuel Home (UX/UI Design Bible
/// Section 5.10: "Entry points: Fuel tab; Today's quick-add" — both
/// named as entry points into Fuel *Home*, not directly into meal
/// capture, which is Fuel Home's own primary action). "Log water" opens
/// the real [WaterLogSheet] built for Fuel — reused here rather than
/// duplicated, a cross-feature import in the same spirit as `AppShell`'s
/// own pre-existing one into Today. "Add a note" has no destination
/// anywhere in this app yet, so it still surfaces the honest "not built
/// yet" signal `TodayScreen`'s own deferred actions use.
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
            showAppBottomSheet<void>(
              context: context,
              builder: (BuildContext context) => const WaterLogSheet(),
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
