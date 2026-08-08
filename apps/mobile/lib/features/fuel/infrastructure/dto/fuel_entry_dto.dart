import '../../../../core/mapping/mapping.dart';
import '../../domain/fuel_models.dart';

/// Mirrors `NutritionResponse` (`backend/app/api/schemas/nutrition.py`)
/// field-for-field, per `docs/adr/0045-shared-api-mapping-convention.md`
/// — this module is the real owner of every nutrition field (unlike
/// Today's minimal `ReadinessSummaryDto`, which reads one field from a
/// response another feature owns), so [FuelEntryDto] carries all of
/// them, the same "a DTO models what a feature consumes" reasoning
/// `ReadinessEntryDto` (`docs/adr/0047`) already applied to a feature
/// that consumes everything.
class FuelEntryDto {
  const FuelEntryDto({
    required this.nutritionId,
    required this.userId,
    required this.nutritionDate,
    required this.recordedAt,
    required this.mealType,
    required this.source,
    required this.calories,
    required this.protein,
    required this.carbohydrates,
    required this.fat,
    required this.fiber,
    required this.sugar,
    required this.waterIntake,
    required this.notes,
    required this.updatedAt,
  });

  factory FuelEntryDto.fromJson(Map<String, dynamic> json) {
    return FuelEntryDto(
      nutritionId: json.requireString('nutrition_id'),
      userId: json.requireString('user_id'),
      nutritionDate: parseApiDate(json.requireString('nutrition_date')),
      recordedAt: parseApiDateTime(json.requireString('recorded_at')),
      mealType: json.optionalString('meal_type'),
      source: json.optionalString('source'),
      calories: json.optionalDouble('calories'),
      protein: json.optionalDouble('protein'),
      carbohydrates: json.optionalDouble('carbohydrates'),
      fat: json.optionalDouble('fat'),
      fiber: json.optionalDouble('fiber'),
      sugar: json.optionalDouble('sugar'),
      waterIntake: json.optionalDouble('water_intake'),
      notes: json.requireString('notes'),
      updatedAt: _optionalDateTime(json.optionalString('updated_at')),
    );
  }

  final String nutritionId;
  final String userId;
  final DateTime nutritionDate;
  final DateTime recordedAt;
  final String? mealType;
  final String? source;
  final double? calories;
  final double? protein;
  final double? carbohydrates;
  final double? fat;
  final double? fiber;
  final double? sugar;
  final double? waterIntake;
  final String notes;
  final DateTime? updatedAt;

  FuelEntry toDomain() {
    return FuelEntry(
      nutritionId: nutritionId,
      nutritionDate: nutritionDate,
      recordedAt: recordedAt,
      mealType: mealType == null ? null : MealType.fromWire(mealType!),
      source: source == null ? null : NutritionSource.fromWire(source!),
      calories: calories,
      protein: protein,
      carbohydrates: carbohydrates,
      fat: fat,
      fiber: fiber,
      sugar: sugar,
      waterIntake: waterIntake,
      notes: notes,
      updatedAt: updatedAt,
    );
  }

  static DateTime? _optionalDateTime(String? value) =>
      value == null ? null : parseApiDateTime(value);
}
