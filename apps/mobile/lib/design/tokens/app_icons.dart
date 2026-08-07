import 'package:flutter/widgets.dart';

/// The icon system — a curated allow-list of semantic names mapped to
/// [IconData], per the UX/UI Design Bible ("a single, consistent,
/// functional icon set — no decorative icons"; "every icon must improve
/// comprehension, never use icons for decoration").
///
/// Two decisions this file exists to enforce architecturally, not just by
/// convention:
///
/// 1. **No new icon package or bundled font.** Flutter ships the
///    classic Material Icons font in the framework itself — free,
///    zero bundle-size cost, and (unlike a pub package such as
///    `material_symbols_icons`) guaranteed to already be correct, since
///    it is the same font the existing shell/navigation code already
///    uses. Pulling in the newer "Material Symbols" family for a
///    marginally more modern glyph style was considered and rejected:
///    it is an extra dependency, an extra font asset, and extra
///    unverifiable surface area for a visual difference few users would
///    ever consciously notice.
/// 2. **Where a glyph genuinely has both an outline and a filled form**
///    (a shape — a circle, a bubble, a pin, a bell — where the two forms
///    are visually distinct), the outline form is the default/inactive
///    state and the filled form is the selected/emphasis state, never
///    mixed with a third style. This is a *functional* signal (this item
///    is currently active), not decoration — see
///    `lib/shell/app_shell.dart`'s existing bottom navigation, which
///    already follows exactly this pattern for its five tab icons; this
///    file formalizes it and reuses those exact glyphs rather than
///    picking new ones. **Where a glyph is inherently a single linear
///    stroke** (an arrow, a chevron, a plus sign, an ellipsis) — where
///    Material does not publish a meaningfully distinct outline/filled
///    pair — this file uses that one canonical glyph rather than forcing
///    a style suffix that would not change how the icon looks.
///
/// Call sites reference [AppIcons.today], never `Icons.today_outlined`
/// directly — reaching directly into Flutter's full `Icons` class from a
/// feature screen is exactly how an icon set drifts inconsistent over
/// time (one screen's author picks a slightly different variant of a
/// conceptually identical glyph than another screen's author did).
/// Adding an icon to this file is a small, deliberate, reviewable step;
/// that friction is intentional.
abstract final class AppIcons {
  // --- Navigation (outline / filled pairs, matching app_shell.dart) ---
  static const IconData today = Icons.today_outlined;
  static const IconData todaySelected = Icons.today;
  static const IconData train = Icons.fitness_center_outlined;
  static const IconData trainSelected = Icons.fitness_center;
  static const IconData fuel = Icons.restaurant_outlined;
  static const IconData fuelSelected = Icons.restaurant;
  static const IconData progress = Icons.show_chart_outlined;
  static const IconData progressSelected = Icons.show_chart;
  // `chat_bubble`/`chat_bubble_outline` were this pair's original glyphs,
  // chosen when Coach was still scaffolded as a placeholder describing
  // itself as "Coach conversation" (see the old `CoachScreen`'s own
  // pre-Sprint-9 doc comment). The Coach module's real build directive
  // is explicit that Coach is not a chatbot and must never read as one —
  // "insights," not "conversation," is what `CoachHomeScreen` actually
  // shows (a feed of real, rule-engine-derived advisory signals, filtered
  // by Recovery/Nutrition/Training). A chat-bubble glyph on the tab bar
  // would visually promise the one interaction model this module
  // explicitly forbids, so this pair was changed alongside the module's
  // real build — see `docs/adr/0041-coach-module.md`.
  static const IconData coach = Icons.insights_outlined;
  static const IconData coachSelected = Icons.insights;

  // --- Global chrome ---
  static const IconData search = Icons.search;
  static const IconData notifications = Icons.notifications_outlined;
  static const IconData settings = Icons.account_circle_outlined;
  static const IconData location = Icons.place_outlined;
  static const IconData close = Icons.close;
  static const IconData back = Icons.arrow_back_ios_new;

  // --- Feedback / state (shape-based — outline form; filled reserved for
  // a rare, deliberate emphasis case such as a completed success state) ---
  static const IconData success = Icons.check_circle_outline;
  static const IconData successFilled = Icons.check_circle;
  static const IconData warning = Icons.error_outline;
  static const IconData danger = Icons.cancel_outlined;
  static const IconData info = Icons.info_outline;

  // --- Common actions (single-stroke glyphs — one canonical form) ---
  static const IconData add = Icons.add;
  static const IconData edit = Icons.edit_outlined;
  static const IconData delete = Icons.delete_outline;
  static const IconData more = Icons.more_horiz;
  static const IconData chevronRight = Icons.chevron_right;
  static const IconData expand = Icons.expand_more;
  static const IconData collapse = Icons.expand_less;
  static const IconData retry = Icons.refresh;

  // --- Progress module (single-stroke glyphs) ---
  //
  // [trendUp]/[trendDown]/[trendFlat] are always paired with plain text
  // (e.g. "0.2 kg vs last check-in") and the neutral `onSurfaceVariant`
  // color, never a success/danger tint — per the Bible's explicit
  // rejection of red/green pass-fail framing on body metrics (Section
  // 11), a rising or falling number is a fact, not good or bad news the
  // icon should editorialize about.
  static const IconData trendUp = Icons.arrow_upward;
  static const IconData trendDown = Icons.arrow_downward;
  static const IconData trendFlat = Icons.remove;
  static const IconData camera = Icons.camera_alt_outlined;
  static const IconData compare = Icons.compare_outlined;
}
