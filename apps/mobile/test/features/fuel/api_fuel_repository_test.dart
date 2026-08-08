import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gym_companion_mobile/core/mapping/mapping.dart';
import 'package:gym_companion_mobile/core/network/network.dart';
import 'package:gym_companion_mobile/features/fuel/domain/fuel_models.dart';
import 'package:gym_companion_mobile/features/fuel/infrastructure/api_fuel_repository.dart';

import '../../core/network/fakes/fake_http_client_adapter.dart';

/// [ApiFuelRepository] against the same hand-written
/// [FakeHttpClientAdapter] `ApiTodayRepository`'s/`ApiReadinessRepository`
/// 's/`ApiTrainRepository`'s own tests already established — see that
/// file's own doc comment for why (proves the real `ApiClient`/`Dio`
/// pipeline, not a hand-rolled repository-level fake).
ApiClient _clientWith(HttpClientAdapter adapter) {
  final Dio dio = Dio(BaseOptions(baseUrl: 'http://test'));
  dio.httpClientAdapter = adapter;
  return ApiClient(dio: dio);
}

Map<String, dynamic> _entryJson({
  String id = 'n1',
  required String nutritionDate,
  String? mealType,
  String? source,
  double? calories,
  double? protein,
  double? carbohydrates,
  double? fat,
  double? fiber,
  double? sugar,
  double? waterIntake,
  String notes = '',
}) {
  return <String, dynamic>{
    'nutrition_id': id,
    'user_id': 'u1',
    'nutrition_date': nutritionDate,
    'recorded_at': '2026-08-08T08:00:00+00:00',
    'meal_type': mealType,
    'source': source,
    'calories': calories,
    'protein': protein,
    'carbohydrates': carbohydrates,
    'fat': fat,
    'fiber': fiber,
    'sugar': sugar,
    'water_intake': waterIntake,
    'notes': notes,
    'updated_at': null,
  };
}

void main() {
  group('fetchHome', () {
    test('maps a real GET /api/v1/nutrition list, filtering to today, newest first', () async {
      final String todayKey = apiDateString(DateTime.now());
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        FakeResponse(
          body: <Map<String, dynamic>>[
            _entryJson(id: 'n-old', nutritionDate: '2026-08-01', calories: 300),
            _entryJson(id: 'n-today-early', nutritionDate: todayKey, calories: 400),
            _entryJson(id: 'n-today-late', nutritionDate: todayKey, waterIntake: 500),
          ],
        ),
      ]);
      final ApiFuelRepository repo = ApiFuelRepository(_clientWith(adapter));

      final FuelHomeViewState state = await repo.fetchHome();

      expect(state.todayEntries.length, 2);
      expect(state.hasLoggedAnyMealEver, isTrue);
      expect(state.proteinConsistencyLabel, isNull);
      expect(state.isOffline, isFalse);
    });

    test('maps every real field, including enum meal_type and source', () async {
      final String todayKey = apiDateString(DateTime.now());
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        FakeResponse(
          body: <Map<String, dynamic>>[
            _entryJson(
              nutritionDate: todayKey,
              mealType: 'breakfast',
              source: 'manual',
              calories: 420,
              protein: 28,
              carbohydrates: 45,
              fat: 14,
              fiber: 5,
              sugar: 10,
              notes: 'Greek yogurt, oats, berries',
            ),
          ],
        ),
      ]);
      final ApiFuelRepository repo = ApiFuelRepository(_clientWith(adapter));

      final FuelHomeViewState state = await repo.fetchHome();
      final FuelEntry entry = state.todayEntries.single;

      expect(entry.mealType, MealType.breakfast);
      expect(entry.source, NutritionSource.manual);
      expect(entry.calories, 420);
      expect(entry.protein, 28);
      expect(entry.notes, 'Greek yogurt, oats, berries');
      expect(entry.isMeal, isTrue);
      expect(entry.isWaterOnly, isFalse);
    });

    test('zero entries has never logged any meal', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(body: <Map<String, dynamic>>[]),
      ]);
      final ApiFuelRepository repo = ApiFuelRepository(_clientWith(adapter));

      final FuelHomeViewState state = await repo.fetchHome();

      expect(state.hasLoggedAnyMealEver, isFalse);
      expect(state.todayEntries, isEmpty);
    });

    test('a network failure propagates as ApiException', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(throwConnectionError: true),
      ]);
      final ApiFuelRepository repo = ApiFuelRepository(_clientWith(adapter));

      expect(repo.fetchHome(), throwsA(isA<ApiException>()));
    });
  });

  group('logMeal', () {
    test('posts only the submitted macro fields plus meal_type, and returns real warnings',
        () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        FakeResponse(
          statusCode: 201,
          body: <String, dynamic>{
            'id': 'new-nutrition-id',
            'warnings': <String>['[warning] Protein intake of 30 g is below the minimum of 50 g.'],
          },
        ),
      ]);
      final ApiFuelRepository repo = ApiFuelRepository(_clientWith(adapter));

      final FuelLogResult result = await repo.logMeal(
        date: DateTime(2026, 8, 8),
        mealType: MealType.breakfast,
        calories: 420,
        protein: 30,
        notes: 'Oats',
      );

      expect(result.warnings, <String>['[warning] Protein intake of 30 g is below the minimum of 50 g.']);
      expect(result.entry.nutritionId, 'new-nutrition-id');
      expect(result.entry.mealType, MealType.breakfast);
      expect(result.entry.calories, 420);
      expect(result.entry.notes, 'Oats');
      // Echoed, not fetched — see this repository's own doc comment for
      // why `source` is null: the request never sent one.
      expect(result.entry.source, isNull);

      final RequestOptions sent = adapter.requests.single;
      expect(sent.path, contains('/api/v1/nutrition'));
      expect(sent.method, 'POST');
      final Map<String, dynamic> body = sent.data as Map<String, dynamic>;
      expect(body['nutrition_date'], apiDateString(DateTime(2026, 8, 8)));
      expect(body['meal_type'], 'breakfast');
      expect(body['calories'], 420);
      expect(body['protein'], 30);
      expect(body['notes'], 'Oats');
      expect(body.containsKey('source'), isFalse);
      expect(body.containsKey('carbohydrates'), isFalse);
    });

    test('an empty warnings list on a clean log is not an error', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        const FakeResponse(
          statusCode: 201,
          body: <String, dynamic>{'id': 'n-clean', 'warnings': <String>[]},
        ),
      ]);
      final ApiFuelRepository repo = ApiFuelRepository(_clientWith(adapter));

      final FuelLogResult result = await repo.logMeal(date: DateTime(2026, 8, 8));

      expect(result.warnings, isEmpty);
    });

    test('a validation failure (real 400) propagates as ApiException', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        FakeResponse(statusCode: 400, body: <String, dynamic>{'detail': 'invalid calories'}),
      ]);
      final ApiFuelRepository repo = ApiFuelRepository(_clientWith(adapter));

      expect(repo.logMeal(date: DateTime(2026, 8, 8)), throwsA(isA<ApiException>()));
    });
  });

  group('logWater', () {
    test('posts only nutrition_date and water_intake', () async {
      final FakeHttpClientAdapter adapter = FakeHttpClientAdapter(<FakeResponse>[
        FakeResponse(
          statusCode: 201,
          body: <String, dynamic>{'id': 'n-water', 'warnings': <String>[]},
        ),
      ]);
      final ApiFuelRepository repo = ApiFuelRepository(_clientWith(adapter));

      final FuelEntry entry = await repo.logWater(date: DateTime(2026, 8, 8), amountMl: 500);

      expect(entry.nutritionId, 'n-water');
      expect(entry.waterIntake, 500);
      expect(entry.isWaterOnly, isTrue);
      expect(entry.source, isNull);

      final Map<String, dynamic> body = adapter.requests.single.data as Map<String, dynamic>;
      expect(body.keys, <String>['nutrition_date', 'water_intake']);
      expect(body['water_intake'], 500);
    });
  });
}
