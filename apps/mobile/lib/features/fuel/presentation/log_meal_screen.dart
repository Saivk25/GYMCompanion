import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../design/design.dart';
import '../../../shared/presentation/widgets/not_connected_placeholder.dart';
import '../application/fuel_controller.dart';
import '../domain/fuel_models.dart';

enum _CaptureMode { photo, text, menu }

/// Log a meal — the Bible's "Meal capture" (Section 5.11 catalog) and
/// "Meal Review/Confirm" (Section 5.3) collapsed into one screen.
///
/// ## Why one screen, not two
///
/// Section 5.3's own spec assumes an AI vision/interpretation step
/// happens *between* capture and confirm ("let the user confirm, correct,
/// or reject the AI's reading… every claim carries a confidence tag").
/// `backend/app/api/schemas/nutrition.py`'s `RecordNutritionRequest` has
/// no confidence field, no photo field, and `NutritionSource` has no
/// `photo`/`vision` value at all — only `manual`/`barcode`/`import`.
/// There is no AI read to review, so capture and confirm are the same
/// user action: type the numbers, submit. Building a separate,
/// artificial "confirm this AI reading" screen with nothing real to
/// confirm would be exactly the "fake successful operation" this
/// project's own directive forbids.
///
/// Photo and Menu modes are real, visible options — not hidden — but
/// each shows [NotConnectedPlaceholder] instead of a camera/vision flow,
/// with a direct path to Text mode. This is not a workaround invented
/// for this gap: the Bible's own empty-states table already prescribes
/// exactly this fallback for a *denied camera permission* — "text/menu-
/// typing entry remains fully available, framed as an equal option, not
/// a degraded fallback" (Section 15) — the same framing applies whether
/// the camera is unavailable for a permissions reason or because no
/// vision backend exists yet to send the photo to.
class LogMealScreen extends ConsumerStatefulWidget {
  const LogMealScreen({super.key});

  @override
  ConsumerState<LogMealScreen> createState() => _LogMealScreenState();
}

class _LogMealScreenState extends ConsumerState<LogMealScreen> {
  _CaptureMode _mode = _CaptureMode.text;
  late MealType _mealType;
  bool _isSubmitting = false;

  final TextEditingController _calories = TextEditingController();
  final TextEditingController _protein = TextEditingController();
  final TextEditingController _carbs = TextEditingController();
  final TextEditingController _fat = TextEditingController();
  final TextEditingController _fiber = TextEditingController();
  final TextEditingController _sugar = TextEditingController();
  final TextEditingController _notes = TextEditingController();

  @override
  void initState() {
    super.initState();
    _mealType = _defaultMealTypeForNow();
  }

  @override
  void dispose() {
    _calories.dispose();
    _protein.dispose();
    _carbs.dispose();
    _fat.dispose();
    _fiber.dispose();
    _sugar.dispose();
    _notes.dispose();
    super.dispose();
  }

  static MealType _defaultMealTypeForNow() {
    final int hour = DateTime.now().hour;
    if (hour < 11) return MealType.breakfast;
    if (hour < 15) return MealType.lunch;
    if (hour < 20) return MealType.dinner;
    return MealType.snack;
  }

  bool get _canSubmit => double.tryParse(_calories.text) != null;

  Future<void> _submit() async {
    setState(() => _isSubmitting = true);
    try {
      await ref.read(fuelHomeControllerProvider.notifier).logMeal(
            date: DateTime.now(),
            mealType: _mealType,
            calories: double.tryParse(_calories.text),
            protein: double.tryParse(_protein.text),
            carbohydrates: double.tryParse(_carbs.text),
            fat: double.tryParse(_fat.text),
            fiber: double.tryParse(_fiber.text),
            sugar: double.tryParse(_sugar.text),
            notes: _notes.text,
          );
      if (!mounted) return;
      Navigator.of(context).pop();
    } catch (_) {
      if (!mounted) return;
      setState(() => _isSubmitting = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Couldn't log this meal. Try again.")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(AppIcons.back),
          tooltip: 'Back',
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Log a meal'),
        actions: <Widget>[
          IconButton(
            icon: const Icon(AppIcons.search),
            tooltip: 'Search foods',
            onPressed: () => context.push('/fuel/search'),
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          children: <Widget>[
            AppSegmentedControl<_CaptureMode>(
              segments: const <(_CaptureMode, String)>[
                (_CaptureMode.photo, 'Photo'),
                (_CaptureMode.text, 'Text'),
                (_CaptureMode.menu, 'Menu'),
              ],
              selected: _mode,
              onChanged: (_CaptureMode m) => setState(() => _mode = m),
            ),
            const SizedBox(height: AppSpacing.xl),
            switch (_mode) {
              _CaptureMode.text => _ManualEntryForm(
                  mealType: _mealType,
                  onMealTypeChanged: (MealType t) => setState(() => _mealType = t),
                  calories: _calories,
                  protein: _protein,
                  carbs: _carbs,
                  fat: _fat,
                  fiber: _fiber,
                  sugar: _sugar,
                  notes: _notes,
                  onChanged: () => setState(() {}),
                ),
              _CaptureMode.photo => const NotConnectedPlaceholder(
                  title: 'Photo capture not connected yet',
                  message:
                      'Reading a meal photo needs a vision AI backend that '
                      "doesn't exist yet. Text entry works the same as "
                      'photo would — nothing here is a degraded fallback.',
                ),
              _CaptureMode.menu => const NotConnectedPlaceholder(
                  title: 'Menu reading not connected yet',
                  message:
                      'Interpreting a mess-menu photo needs a vision AI '
                      "backend that doesn't exist yet. Text entry works the "
                      'same as menu reading would.',
                ),
            },
            if (_mode != _CaptureMode.text) ...<Widget>[
              const SizedBox(height: AppSpacing.lg),
              Center(
                child: AppButton(
                  label: 'Use text entry instead',
                  variant: AppButtonVariant.secondary,
                  fullWidth: false,
                  onPressed: () => setState(() => _mode = _CaptureMode.text),
                ),
              ),
            ],
            if (_mode == _CaptureMode.text) ...<Widget>[
              const SizedBox(height: AppSpacing.xxl),
              AppButton(
                label: 'Log meal',
                isLoading: _isSubmitting,
                onPressed: _canSubmit ? _submit : null,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _ManualEntryForm extends StatelessWidget {
  const _ManualEntryForm({
    required this.mealType,
    required this.onMealTypeChanged,
    required this.calories,
    required this.protein,
    required this.carbs,
    required this.fat,
    required this.fiber,
    required this.sugar,
    required this.notes,
    required this.onChanged,
  });

  final MealType mealType;
  final ValueChanged<MealType> onMealTypeChanged;
  final TextEditingController calories;
  final TextEditingController protein;
  final TextEditingController carbs;
  final TextEditingController fat;
  final TextEditingController fiber;
  final TextEditingController sugar;
  final TextEditingController notes;
  final VoidCallback onChanged;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        Text('Meal', style: textTheme.titleMedium),
        const SizedBox(height: AppSpacing.sm),
        AppSegmentedControl<MealType>(
          segments: <(MealType, String)>[
            for (final MealType type in MealType.values) (type, type.label),
          ],
          selected: mealType,
          onChanged: onMealTypeChanged,
        ),
        const SizedBox(height: AppSpacing.xl),
        Row(
          children: <Widget>[
            Expanded(
              child: AppTextField(
                label: 'Calories',
                controller: calories,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                inputFormatters: <TextInputFormatter>[
                  FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d*')),
                ],
                textInputAction: TextInputAction.next,
                onChanged: (_) => onChanged(),
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: AppTextField(
                label: 'Protein (g)',
                controller: protein,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                inputFormatters: <TextInputFormatter>[
                  FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d*')),
                ],
                textInputAction: TextInputAction.next,
              ),
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.sm),
        Row(
          children: <Widget>[
            Expanded(
              child: AppTextField(
                label: 'Carbs (g)',
                controller: carbs,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                inputFormatters: <TextInputFormatter>[
                  FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d*')),
                ],
                textInputAction: TextInputAction.next,
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: AppTextField(
                label: 'Fat (g)',
                controller: fat,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                inputFormatters: <TextInputFormatter>[
                  FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d*')),
                ],
                textInputAction: TextInputAction.next,
              ),
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.xl),
        Text(
          'Optional detail',
          style: textTheme.labelMedium?.copyWith(color: colorScheme.onSurfaceVariant),
        ),
        const SizedBox(height: AppSpacing.sm),
        Row(
          children: <Widget>[
            Expanded(
              child: AppTextField(
                label: 'Fiber (g)',
                controller: fiber,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                inputFormatters: <TextInputFormatter>[
                  FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d*')),
                ],
                textInputAction: TextInputAction.next,
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: AppTextField(
                label: 'Sugar (g)',
                controller: sugar,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                inputFormatters: <TextInputFormatter>[
                  FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d*')),
                ],
                textInputAction: TextInputAction.next,
              ),
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.lg),
        AppTextField(
          label: 'Notes (optional)',
          controller: notes,
          textInputAction: TextInputAction.done,
          onSubmitted: (_) => FocusScope.of(context).unfocus(),
        ),
      ],
    );
  }
}
