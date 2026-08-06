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
  });
}
