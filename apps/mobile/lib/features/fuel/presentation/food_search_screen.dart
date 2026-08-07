import 'package:flutter/material.dart';

import '../../../design/design.dart';
import '../../../shared/presentation/widgets/not_connected_placeholder.dart';

/// Food Search / Selection — no food database or barcode-lookup endpoint
/// exists anywhere in the backend (`NutritionSource.barcode` is a real
/// enum value with no route behind it — a documented-but-unimplemented
/// source, not a live one). A real, reachable screen with an honest
/// "not connected yet" placeholder, per this module's directive: search
/// gets a placeholder rather than being skipped, and manual entry
/// (`LogMealScreen`) remains the fully real path.
class FoodSearchScreen extends StatelessWidget {
  const FoodSearchScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(AppIcons.back),
          tooltip: 'Back',
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Search foods'),
      ),
      body: const SafeArea(
        child: Center(
          child: NotConnectedPlaceholder(
            title: 'Food search not connected yet',
            message:
                'Searching a food database needs a backend endpoint that '
                "doesn't exist yet. Log a meal with manual entry in the "
                'meantime — it works exactly the same either way.',
          ),
        ),
      ),
    );
  }
}
