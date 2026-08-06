/// The single entry point to Gym Companion's design system — tokens,
/// theme, and reusable components. Every screen should import this one
/// file (`import 'package:gym_companion_mobile/design/design.dart';`)
/// rather than reaching into `lib/design/tokens/`, `lib/design/theme/`,
/// or `lib/design/components/` individually.
///
/// See `docs/adr/0034-flutter-design-system.md` (repository root) for the
/// full reasoning behind every decision in this package, and this
/// package's own file-level doc comments for the reasoning behind each
/// individual token, theme, and component.
library;

export 'components/components.dart';
export 'theme/app_color_scheme.dart';
export 'theme/app_semantic_colors.dart';
export 'theme/app_text_theme.dart';
export 'theme/app_theme.dart';
export 'tokens/tokens.dart';
