import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/core/mapping/api_date_time.dart';

void main() {
  group('parseApiDateTime', () {
    test('parses a UTC-offset ISO 8601 string and normalizes to UTC', () {
      final DateTime result = parseApiDateTime('2026-08-08T10:30:00+00:00');
      expect(result.isUtc, isTrue);
      expect(result.year, 2026);
      expect(result.month, 8);
      expect(result.day, 8);
      expect(result.hour, 10);
      expect(result.minute, 30);
    });

    test('normalizes a non-UTC offset to UTC on parse', () {
      final DateTime result = parseApiDateTime('2026-08-08T10:30:00+05:00');
      expect(result.isUtc, isTrue);
      expect(result.hour, 5);
    });
  });

  group('parseApiDate', () {
    test('parses a bare calendar date', () {
      final DateTime result = parseApiDate('2026-08-08');
      expect(result.year, 2026);
      expect(result.month, 8);
      expect(result.day, 8);
    });
  });

  group('apiDateString', () {
    test('formats a date as YYYY-MM-DD', () {
      expect(apiDateString(DateTime(2026, 8, 8)), '2026-08-08');
    });

    test('zero-pads single-digit month and day', () {
      expect(apiDateString(DateTime(2026, 1, 5)), '2026-01-05');
    });

    test('round-trips with parseApiDate', () {
      const String original = '2026-03-14';
      expect(apiDateString(parseApiDate(original)), original);
    });

    test('ignores time-of-day when formatting', () {
      final DateTime withTime = DateTime(2026, 8, 8, 23, 59, 59);
      expect(apiDateString(withTime), '2026-08-08');
    });
  });
}
