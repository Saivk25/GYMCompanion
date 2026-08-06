import 'package:flutter/material.dart';

import '../../../../design/design.dart';
import '../../../../shared/domain/session_tier.dart';

/// The explicit tier choice the Pre-session screen offers (UX/UI Design
/// Bible catalog: "Review today's tier before starting. Choose tier and
/// start.") — distinct from [AppSegmentedControl]: a tier choice carries
/// a real description per option the user should read before committing,
/// not just a short tab label, so this renders as a flat, selectable
/// three-row list inside one [AppCard] rather than a pill control.
///
/// The user may always choose a *lower* tier than the resolved default
/// (Domain Model Bible: never higher without rule permission) — this
/// widget does not enforce that itself (it has no concept of "the
/// resolved default's ceiling"); `PreSessionScreen` is responsible for
/// only ever constructing it with tiers the workout actually allows.
class TierPicker extends StatelessWidget {
  const TierPicker({required this.selected, required this.onChanged, super.key});

  final SessionTier selected;
  final ValueChanged<SessionTier> onChanged;

  @override
  Widget build(BuildContext context) {
    return AppCard(
      padding: EdgeInsets.zero,
      elevation: AppElevationLevel.flat,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          for (final SessionTier tier in SessionTier.values) ...<Widget>[
            _TierRow(
              tier: tier,
              isSelected: tier == selected,
              onTap: () => onChanged(tier),
            ),
            if (tier != SessionTier.values.last)
              Divider(height: 1, color: Theme.of(context).colorScheme.outlineVariant),
          ],
        ],
      ),
    );
  }
}

class _TierRow extends StatelessWidget {
  const _TierRow({required this.tier, required this.isSelected, required this.onTap});

  final SessionTier tier;
  final bool isSelected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final TextTheme textTheme = Theme.of(context).textTheme;
    final ColorScheme colorScheme = Theme.of(context).colorScheme;
    final AppSemanticColors semantic = Theme.of(context).semanticColors;

    return Semantics(
      button: true,
      selected: isSelected,
      label: '${tier.label}: ${tier.description}',
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          child: ConstrainedBox(
            constraints: const BoxConstraints(minHeight: kMinInteractiveDimension),
            child: Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.lg,
                vertical: AppSpacing.md,
              ),
              child: Row(
                children: <Widget>[
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: <Widget>[
                        Text(
                          tier.label,
                          style: textTheme.titleMedium?.copyWith(
                            color: isSelected ? semantic.selected : null,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          tier.description,
                          style: textTheme.bodySmall?.copyWith(color: colorScheme.onSurfaceVariant),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: AppSpacing.sm),
                  Icon(
                    isSelected ? AppIcons.successFilled : AppIcons.chevronRight,
                    color: isSelected ? semantic.success : colorScheme.onSurfaceVariant,
                    size: 20,
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
