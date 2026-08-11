import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../design/design.dart';
import '../application/readiness_controller.dart';
import '../domain/readiness_models.dart';
import 'widgets/readiness_entry_tile.dart';

/// Recovery Timeline — every real logged check-in, chronological, newest
/// first. Also satisfies "Recovery History" from this module's own build
/// list: the Bible names no separate history screen alongside a
/// timeline for any comparable module (the same reasoning Progress's own
/// ADR 0039 Decision 4 applied to "Nutrition History" — a second,
/// differently-named screen showing the same list would be inventing a
/// screen, not building one the Bible asks for). Reads from the same
/// [readinessHomeControllerProvider] state Readiness Home already
/// holds — the full entry list Readiness Home receives from
/// [ReadinessRepository.fetchHome] already carries this screen's
/// content, so a second fetch would only duplicate data already in
/// memory.
class ReadinessTimelineScreen extends ConsumerWidget {
  const ReadinessTimelineScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final AsyncValue<ReadinessHomeViewState> state = ref.watch(readinessHomeControllerProvider);

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(AppIcons.back),
          tooltip: 'Back',
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Recovery timeline'),
      ),
      body: state.when(
        loading: () => const Center(child: AppLoadingIndicator()),
        error: (Object error, StackTrace stackTrace) => Center(
          child: AppErrorState(
            message: "This timeline couldn't be loaded.",
            onRetry: () => ref.read(readinessHomeControllerProvider.notifier).refresh(),
          ),
        ),
        data: (ReadinessHomeViewState data) {
          if (data.entries.isEmpty) {
            return const SafeArea(
              child: Center(
                child: AppEmptyState(
                  icon: AppIcons.progress,
                  title: 'No check-ins yet',
                  message: 'Every check-in you submit will show up here.',
                ),
              ),
            );
          }
          // TD-0010 (`docs/TECH_DEBT.md`): previously an `AppCard` sized to
          // its `Column`'s content, wrapping an eager `for` comprehension
          // that built every one of the user's check-ins — potentially
          // hundreds — on every visit and every rebuild. `ListView.builder`
          // below only ever builds what's on (or near) screen, but a
          // `ListView.builder` can't be handed an `AppCard`-sized child the
          // way the old eager `Column` could — its content height isn't
          // known until scrolled. The `DecoratedBox`/`ClipRRect` pairing
          // recreates `AppCard`'s exact fill, corner radius, and shadow
          // (`AppColorScheme.surfaceAt`, `AppElevation.shadowsFor`) around
          // the *available space* instead of around the *content*, so the
          // grouped-card look is preserved without needing per-row corner-
          // radius logic. The one visible trade-off: a short history now
          // renders as a tall card with empty space below the last row,
          // rather than a card that shrinks to fit — judged a reasonable,
          // common ("grouped list") pattern rather than a regression.
          final ColorScheme colorScheme = Theme.of(context).colorScheme;
          return SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.lg),
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: AppColorScheme.surfaceAt(colorScheme, AppElevationLevel.raised),
                  borderRadius: AppRadius.radiusMd,
                  boxShadow: AppElevation.shadowsFor(
                    AppElevationLevel.raised,
                    brightness: colorScheme.brightness,
                    shadowColor: colorScheme.shadow,
                  ),
                ),
                child: ClipRRect(
                  borderRadius: AppRadius.radiusMd,
                  child: ListView.builder(
                    itemCount: data.entries.length,
                    itemBuilder: (BuildContext context, int index) {
                      final ReadinessEntry entry = data.entries[index];
                      return ReadinessEntryTile(
                        entry: entry,
                        onTap: () => context.push('/readiness/entry/${entry.readinessId}'),
                      );
                    },
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
