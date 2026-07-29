import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/app.dart';

void main() {
  testWidgets('lands on Today and can navigate to Train via the bottom bar', (
    tester,
  ) async {
    await tester.pumpWidget(const ProviderScope(child: GymCompanionApp()));
    await tester.pumpAndSettle();

    expect(find.text('Today'), findsWidgets);

    await tester.tap(find.text('Train'));
    await tester.pumpAndSettle();

    expect(find.text('Train'), findsWidgets);
  });

  testWidgets('all five tab destinations are present', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: GymCompanionApp()));
    await tester.pumpAndSettle();

    for (final label in ['Today', 'Train', 'Fuel', 'Progress', 'Coach']) {
      expect(find.text(label), findsWidgets);
    }
  });
}
