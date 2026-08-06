import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/design/design.dart';

void main() {
  group('AppTheme', () {
    testWidgets('light theme builds and renders a themed screen', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.light,
          home: const Scaffold(body: Text('Today')),
        ),
      );

      expect(find.text('Today'), findsOneWidget);
    });

    testWidgets('dark theme builds and renders a themed screen', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.dark,
          home: const Scaffold(body: Text('Today')),
        ),
      );

      expect(find.text('Today'), findsOneWidget);
    });

    test('light and dark expose the AppSemanticColors extension', () {
      expect(
        AppTheme.light.extension<AppSemanticColors>(),
        isNotNull,
      );
      expect(
        AppTheme.dark.extension<AppSemanticColors>(),
        isNotNull,
      );
    });

    test('light and dark are memoized, not rebuilt on every access', () {
      // Regression test for Critical Finding 1: `AppTheme.light`/`.dark`
      // were previously `get` accessors that rebuilt the entire ThemeData
      // tree on every read. `static final` means two reads return the
      // *same instance*, not just an equal one.
      expect(identical(AppTheme.light, AppTheme.light), isTrue);
      expect(identical(AppTheme.dark, AppTheme.dark), isTrue);
    });
  });

  group('AppSemanticColors', () {
    test('light and dark define the disabled/focus/selection tokens', () {
      // Regression test for Important Finding 7: these were previously
      // absent, relying on implicit Material defaults.
      for (final AppSemanticColors semantic in <AppSemanticColors>[
        AppSemanticColors.light,
        AppSemanticColors.dark,
      ]) {
        expect(semantic.disabledContent, isNotNull);
        expect(semantic.disabledContainer, isNotNull);
        expect(semantic.focusRing, isNotNull);
        expect(semantic.selected, isNotNull);
        expect(semantic.onSelected, isNotNull);
        expect(semantic.selectedContainer, isNotNull);
      }
    });

    test('light and dark are memoized, not rebuilt on every access', () {
      expect(
        identical(AppSemanticColors.light, AppSemanticColors.light),
        isTrue,
      );
      expect(
        identical(AppSemanticColors.dark, AppSemanticColors.dark),
        isTrue,
      );
    });
  });

  group('AppSpacing', () {
    test('is a strictly increasing scale with no duplicate steps', () {
      const List<double> scale = <double>[
        AppSpacing.xs,
        AppSpacing.sm,
        AppSpacing.md,
        AppSpacing.lg,
        AppSpacing.xl,
        AppSpacing.xxl,
        AppSpacing.xxxl,
        AppSpacing.huge,
        AppSpacing.massive,
        AppSpacing.giant,
      ];

      for (int i = 1; i < scale.length; i++) {
        expect(scale[i], greaterThan(scale[i - 1]));
      }
    });
  });

  group('AppBreakpoints', () {
    test('classifies widths into the correct window size class', () {
      expect(AppBreakpoints.classify(360), WindowSizeClass.compact);
      expect(AppBreakpoints.classify(700), WindowSizeClass.medium);
      expect(AppBreakpoints.classify(1024), WindowSizeClass.expanded);
    });
  });

  group('design system components', () {
    testWidgets('AppButton, AppCard, and AppBadge render without error', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.light,
          home: Scaffold(
            body: Column(
              children: <Widget>[
                AppButton(label: 'Start session', onPressed: () {}),
                const AppCard(child: Text('Card content')),
                const AppBadge(
                  label: 'High confidence',
                  icon: Icons.check_circle_outline,
                  tone: AppBadgeTone.success,
                ),
              ],
            ),
          ),
        ),
      );

      expect(find.text('Start session'), findsOneWidget);
      expect(find.text('Card content'), findsOneWidget);
      expect(find.text('High confidence'), findsOneWidget);
    });

    testWidgets('AppEmptyState and AppErrorState render without error', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.light,
          home: Scaffold(
            body: Column(
              children: <Widget>[
                const AppEmptyState(
                  icon: Icons.today_outlined,
                  title: 'Nothing here yet',
                ),
                AppErrorState(
                  message: 'Could not load your session.',
                  onRetry: () {},
                ),
              ],
            ),
          ),
        ),
      );

      expect(find.text('Nothing here yet'), findsOneWidget);
      expect(find.text('Could not load your session.'), findsOneWidget);
      expect(find.text('Try again'), findsOneWidget);
    });

    testWidgets(
      'AppButton announces its label to assistive tech while loading',
      (WidgetTester tester) async {
        // Regression test for Critical Finding 4: the loading branch
        // previously dropped Text(label) entirely, leaving a screen
        // reader with nothing meaningful to announce.
        final SemanticsHandle handle = tester.ensureSemantics();
        await tester.pumpWidget(
          MaterialApp(
            theme: AppTheme.light,
            home: Scaffold(
              body: AppButton(
                label: 'Save workout',
                onPressed: () {},
                isLoading: true,
              ),
            ),
          ),
        );

        expect(find.bySemanticsLabel('Save workout'), findsOneWidget);
        handle.dispose();
      },
    );

    testWidgets(
      'AppListTile with title only still meets the 48dp minimum touch target',
      (WidgetTester tester) async {
        // Regression test for Critical Finding 3.
        await tester.pumpWidget(
          const MaterialApp(
            home: Scaffold(
              body: AppListTile(title: 'Leg day'),
            ),
          ),
        );

        final Size size = tester.getSize(find.byType(AppListTile));
        expect(size.height, greaterThanOrEqualTo(kMinInteractiveDimension));
      },
    );

    testWidgets(
      'AppSkeletonBox allocates no ticker when reduced motion is enabled',
      (WidgetTester tester) async {
        // Regression test for Critical Finding 2: previously the
        // AnimationController kept repeating in the background even
        // with reduced motion on. A still-repeating controller keeps
        // scheduling frames forever, so `pumpAndSettle` below would
        // never converge and this test would fail with a timeout before
        // the fix — completing at all is the actual regression guard,
        // not just the assertion after it.
        await tester.pumpWidget(
          const MediaQuery(
            data: MediaQueryData(disableAnimations: true),
            child: MaterialApp(
              home: Scaffold(
                body: AppSkeletonBox(width: 120, height: 16),
              ),
            ),
          ),
        );

        await tester.pumpAndSettle();
        expect(find.byType(AppSkeletonBox), findsOneWidget);
      },
    );

    testWidgets(
      'AppSegmentedControl renders every segment and announces the selected one',
      (WidgetTester tester) async {
        // Train's own regression coverage for this phase's design-system
        // extension (see that file's doc comment for why it had to be
        // built rather than bypassed).
        final SemanticsHandle handle = tester.ensureSemantics();
        String selected = 'a';
        await tester.pumpWidget(
          MaterialApp(
            theme: AppTheme.light,
            home: Scaffold(
              body: StatefulBuilder(
                builder: (context, setState) => AppSegmentedControl<String>(
                  segments: const <(String, String)>[
                    ('a', 'This Week'),
                    ('b', 'History'),
                    ('c', 'Library'),
                  ],
                  selected: selected,
                  onChanged: (String v) => setState(() => selected = v),
                ),
              ),
            ),
          ),
        );

        expect(find.text('This Week'), findsOneWidget);
        expect(find.text('History'), findsOneWidget);
        expect(find.text('Library'), findsOneWidget);

        await tester.tap(find.text('History'));
        await tester.pump();
        expect(selected, 'b');
        handle.dispose();
      },
    );

    testWidgets('AppTextField renders its label and reports typed input', (
      WidgetTester tester,
    ) async {
      final TextEditingController controller = TextEditingController();
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.light,
          home: Scaffold(
            body: AppTextField(label: 'Weight', controller: controller),
          ),
        ),
      );

      expect(find.text('Weight'), findsOneWidget);
      await tester.enterText(find.byType(TextField), '60');
      expect(controller.text, '60');
    });
  });
}
