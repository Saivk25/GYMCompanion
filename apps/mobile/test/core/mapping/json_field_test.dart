import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/core/mapping/json_field.dart';

void main() {
  group('required extraction', () {
    test('requireString returns the value when present and typed correctly', () {
      expect(<String, dynamic>{'name': 'Squat'}.requireString('name'), 'Squat');
    });

    test('requireString throws FormatException when missing', () {
      expect(
        () => <String, dynamic>{}.requireString('name'),
        throwsA(isA<FormatException>()),
      );
    });

    test('requireString throws FormatException when wrongly typed', () {
      expect(
        () => <String, dynamic>{'name': 42}.requireString('name'),
        throwsA(isA<FormatException>()),
      );
    });

    test('requireInt accepts a JSON int', () {
      expect(<String, dynamic>{'reps': 10}.requireInt('reps'), 10);
    });

    test('requireInt accepts a whole-number JSON double', () {
      expect(<String, dynamic>{'reps': 10.0}.requireInt('reps'), 10);
    });

    test('requireDouble accepts a JSON int, widened', () {
      expect(<String, dynamic>{'weight': 100}.requireDouble('weight'), 100.0);
    });

    test('requireBool returns the value', () {
      expect(<String, dynamic>{'completed': true}.requireBool('completed'), isTrue);
    });

    test('requireList returns the raw list', () {
      final List<dynamic> result = <String, dynamic>{
        'sets': <int>[1, 2, 3],
      }.requireList('sets');
      expect(result, <int>[1, 2, 3]);
    });

    test('requireObject returns a nested map', () {
      final Map<String, dynamic> result = <String, dynamic>{
        'user': <String, dynamic>{'id': 'u1'},
      }.requireObject('user');
      expect(result, <String, dynamic>{'id': 'u1'});
    });

    test('a missing field error message names the field', () {
      try {
        <String, dynamic>{}.requireString('workout_id');
        fail('expected a FormatException');
      } on FormatException catch (e) {
        expect(e.message, contains('workout_id'));
      }
    });
  });

  group('optional extraction', () {
    test('optionalString returns null when missing', () {
      expect(<String, dynamic>{}.optionalString('goal'), isNull);
    });

    test('optionalString returns null when explicitly JSON null', () {
      expect(<String, dynamic>{'goal': null}.optionalString('goal'), isNull);
    });

    test('optionalString returns the value when present', () {
      expect(<String, dynamic>{'goal': 'Get strong'}.optionalString('goal'), 'Get strong');
    });

    test('optionalInt widens a double', () {
      expect(<String, dynamic>{'count': 3.0}.optionalInt('count'), 3);
    });

    test('optionalDouble widens an int', () {
      expect(<String, dynamic>{'value': 3}.optionalDouble('value'), 3.0);
    });

    test('optionalBool returns null when missing', () {
      expect(<String, dynamic>{}.optionalBool('flag'), isNull);
    });

    test('optionalList returns null when missing', () {
      expect(<String, dynamic>{}.optionalList('items'), isNull);
    });
  });
}
