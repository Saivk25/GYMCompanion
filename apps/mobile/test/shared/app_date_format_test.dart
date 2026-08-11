import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/shared/presentation/app_date_format.dart';

/// Regression coverage for TD-0004 (`docs/TECH_DEBT.md`) — one test per
/// output shape this shared module replaced across nine presentation
/// files, so a future edit here can't silently change what any of those
/// screens render.
void main() {
  group('appWeekdayMonthDay', () {
    test('formats a full weekday, full month, and day', () {
      expect(appWeekdayMonthDay(DateTime(2026, 1, 5)), 'Monday, January 5');
    });
  });

  group('appMonthDayYear', () {
    test('formats a full month, day, and year', () {
      expect(appMonthDayYear(DateTime(2026, 1, 5)), 'January 5, 2026');
    });
  });

  group('appShortMonthDay', () {
    test('formats a short month and day, no year', () {
      expect(appShortMonthDay(DateTime(2026, 1, 5)), 'Jan 5');
    });
  });

  group('appRelativeDay', () {
    final DateTime now = DateTime(2026, 8, 11);

    test('returns Today for the same calendar day', () {
      expect(appRelativeDay(DateTime(2026, 8, 11, 22), now: now), 'Today');
    });

    test('returns Tomorrow for the next calendar day', () {
      expect(appRelativeDay(DateTime(2026, 8, 12), now: now), 'Tomorrow');
    });

    test('returns a short weekday for any other day', () {
      expect(appRelativeDay(DateTime(2026, 8, 14), now: now), 'Fri');
    });
  });

  group('appTimeOfDay', () {
    test('formats a morning time with AM', () {
      expect(appTimeOfDay(DateTime(2026, 1, 1, 9, 5)), '9:05 AM');
    });

    test('formats an afternoon time with PM', () {
      expect(appTimeOfDay(DateTime(2026, 1, 1, 15, 45)), '3:45 PM');
    });

    test('formats midnight as 12 AM', () {
      expect(appTimeOfDay(DateTime(2026, 1, 1)), '12:00 AM');
    });

    test('formats noon as 12 PM', () {
      expect(appTimeOfDay(DateTime(2026, 1, 1, 12)), '12:00 PM');
    });
  });

  group('appMonthDayAtTime', () {
    test('combines the month/day with the clock time', () {
      expect(
        appMonthDayAtTime(DateTime(2026, 1, 5, 15, 45)),
        'January 5 at 3:45 PM',
      );
    });
  });

  group('appDurationMinutes', () {
    test('rounds a seconds value to the nearest minute', () {
      expect(appDurationMinutes(2700), '45 min');
    });

    test('rounds up when past the half-minute mark', () {
      expect(appDurationMinutes(95), '2 min');
    });
  });

  group('appElapsedTime', () {
    test('formats minutes and seconds with a zero-padded seconds field', () {
      expect(appElapsedTime(const Duration(minutes: 12, seconds: 34)), '12:34');
    });

    test('formats a duration under a minute', () {
      expect(appElapsedTime(const Duration(seconds: 7)), '0:07');
    });

    test('does not wrap minutes past 59', () {
      expect(appElapsedTime(const Duration(minutes: 75, seconds: 3)), '75:03');
    });
  });
}
