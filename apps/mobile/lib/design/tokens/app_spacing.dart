/// The spacing scale — the only set of numbers permitted for padding,
/// margin, and gap values anywhere in this app.
///
/// Ten steps, every value a multiple of 4: `4, 8, 12, 16, 20, 24, 32, 40,
/// 48, 64`. This refines the UX/UI Design Bible's own structural rule
/// (Section 10: "a single 8-point-based scale (4/8/16/24/32/48); no
/// arbitrary spacing values anywhere") into a complete working scale —
/// the Bible deliberately specified no pixel values, only the constraint
/// that a designer builds the real scale from. `12`, `20`, `40`, and `64`
/// are the natural interpolations that keep every step on the same 4px
/// grid the Bible's own five illustrative values already sit on, rather
/// than a designer inventing an unrelated set later.
///
/// ## Why a fixed, named scale instead of raw numbers
///
/// A layout built from arbitrary numbers (`17`, `22`, `9`) accumulates
/// inconsistency invisibly — no single screen looks wrong, but nothing
/// lines up with anything else, and that's exactly the "inconsistent
/// spacing" anti-pattern this app is told to avoid on sight. A fixed
/// scale makes misalignment a `flutter analyze`-adjacent code-review
/// question ("why is this `18` and not `16` or `20`?") instead of a
/// silent visual defect only a designer's eye would catch. Every step
/// is also a genuinely distinct, purposeful size — not a dense scale
/// where adjacent steps are indistinguishable in practice — so a call
/// site is never choosing between two options that would have looked
/// identical anyway.
///
/// ## How to read the scale
///
/// - `xs` (4) — the tightest gap that still reads as *a* gap: icon-to-label
///   spacing, the gap between a badge's icon and its text.
/// - `sm` (8) — spacing within a tightly related group: a card's internal
///   gap between a title and its subtitle.
/// - `md` (12) — spacing between related-but-distinct elements: rows in a
///   compact list, chip spacing.
/// - `lg` (16) — the default content padding inside a card or screen edge;
///   the single most commonly used value in this scale by design.
/// - `xl` (20) — the gap between two adjacent cards in a single visual
///   group.
/// - `xxl` (24) — the gap between distinct sections on the same screen.
/// - `xxxl` (32) — major section breaks; the top padding under a screen's
///   persistent app bar before content begins.
/// - `huge` (40) — rare: a hero moment's breathing room (e.g. above a
///   large summary number).
/// - `massive` (48) — rare: full-bleed empty-state vertical centering.
/// - `giant` (64) — reserved for empty/onboarding screens where a large
///   top offset is the entire point.
abstract final class AppSpacing {
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 12;
  static const double lg = 16;
  static const double xl = 20;
  static const double xxl = 24;
  static const double xxxl = 32;
  static const double huge = 40;
  static const double massive = 48;
  static const double giant = 64;
}
