import 'package:flutter/widgets.dart';

/// Primitive color ramps — the *only* file in this design system permitted
/// to contain a literal `Color(0x...)` value.
///
/// Nothing outside `lib/design/` should ever reference [AppColors] directly.
/// Screens and components consume semantic tokens
/// (`AppColorScheme`/`AppSemanticColors` in `lib/design/theme/`), which are
/// themselves built from this file. That indirection is the entire point of
/// a token system: changing the product's accent hue, or retuning a single
/// step of the neutral ramp for contrast, is a one-file edit here that
/// propagates everywhere, rather than a find-and-replace across every
/// screen that hardcoded `Color(0xFF3D5FE0)` inline.
///
/// ## Why these specific colors
///
/// The UX/UI Design Bible (Section 11, "Visual language") calls for
/// "calm," "muted," "no alarm-red overuse," and explicitly rejects
/// red/green pass-fail framing on body metrics. That rules out the two
/// most common default choices for a fitness app: a loud saturated brand
/// color used everywhere, and traffic-light semantic colors borrowed
/// straight from a Material color picker. Two decisions follow from that:
///
/// 1. **One neutral ramp, reused for both light and dark themes** (the
///    same technique GitHub Primer, Stripe, and Linear all use) rather
///    than two unrelated palettes. A single ramp guarantees the two
///    themes are tonally the same product, just inverted — not two
///    different-looking apps that happen to share a codebase.
/// 2. **A single restrained accent** (`signal`), used sparingly for
///    primary actions and focus states, not sprinkled across every
///    element. Reserving color for meaning — not decoration — is the
///    single biggest lever against the "AI-generated dashboard" look,
///    where every card gets its own gradient or accent color because
///    nothing was told not to.
///
/// The neutral ramp carries a slight cool (blue-leaning) undertone rather
/// than a flat, pure gray — flat grays read as an unstyled default
/// (`Colors.grey` in a Material demo); a deliberately tuned undertone is
/// what separates a designed neutral palette from an accidental one.
///
/// Every ramp step is named by its position on a 50-950 scale (the same
/// convention Tailwind, Radix, and Primer use), not by a description like
/// "light gray" — descriptions stop being true the moment a shade is
/// retuned, and a numbered position never lies about its role in the
/// ramp.
abstract final class AppColors {
  // --- Neutral ("slate") — backgrounds, surfaces, borders, text. Reused by
  // both themes: light mode reads the ramp low-to-high, dark mode reads it
  // high-to-low. See `AppColorScheme` for that mapping. ---
  static const Color neutral0 = Color(0xFFFFFFFF);
  static const Color neutral50 = Color(0xFFF8F9FB);
  static const Color neutral100 = Color(0xFFF1F2F5);
  static const Color neutral200 = Color(0xFFE3E5EA);
  static const Color neutral300 = Color(0xFFCDD0D8);
  static const Color neutral400 = Color(0xFFA9AEBA);
  static const Color neutral500 = Color(0xFF82889A);
  static const Color neutral600 = Color(0xFF656B7C);
  static const Color neutral700 = Color(0xFF4E5464);
  static const Color neutral800 = Color(0xFF383C49);
  static const Color neutral900 = Color(0xFF24262F);
  static const Color neutral950 = Color(0xFF16171D);
  // Near-black, not pure #000000 — pure black against a lit screen produces
  // a harsher, lower-quality-feeling contrast than a slightly lifted black;
  // this is the same reason Apple's own dark surfaces are rarely #000.
  static const Color neutral1000 = Color(0xFF0B0C0F);

  // --- Signal (accent) — the one color reserved for primary actions,
  // links, selection, and focus. A confident, slightly desaturated blue:
  // trustworthy and calm rather than energetic, appropriate for a health
  // product where "urgent" and "exciting" are not feelings to reach for. ---
  static const Color signal50 = Color(0xFFEEF2FF);
  static const Color signal100 = Color(0xFFDCE4FF);
  static const Color signal200 = Color(0xFFB9C9FF);
  static const Color signal300 = Color(0xFF8FA5FF);
  static const Color signal400 = Color(0xFF6683FA);
  static const Color signal500 = Color(0xFF3D5FE0);
  static const Color signal600 = Color(0xFF2F4BC2);
  static const Color signal700 = Color(0xFF24399A);
  static const Color signal800 = Color(0xFF1B2C77);
  static const Color signal900 = Color(0xFF141F57);

  // --- Success — reserved for genuine, discrete achievements (a
  // completed session, a PR, a resolved safety flag). Never used for
  // routine "this number went up" framing on a body metric — see the
  // Bible's explicit rejection of red/green pass-fail body-metric
  // coloring, Section 18. A muted forest tone, not a bright "go" green. ---
  static const Color success50 = Color(0xFFEAF6EE);
  static const Color success100 = Color(0xFFD1EBDA);
  static const Color success300 = Color(0xFF7FC79B);
  static const Color success500 = Color(0xFF2F9E5C);
  static const Color success700 = Color(0xFF1F7A45);
  static const Color success900 = Color(0xFF12492A);

  // --- Warning — reduced-capacity / caution states (a Light or Recovery
  // readiness band, a soft data-quality note). A muted ochre, deliberately
  // far from a saturated "danger-adjacent" orange.
  //
  // `warning500` is `0xFFBF832C`, not the more saturated `0xFFC98A2E` an
  // earlier version of this ramp used — the design system review's WCAG
  // audit computed this tone's real contrast against a white surface
  // (the context `AppSemanticColors.warning`'s own doc comment names:
  // "a strong tone for icons/text-on-fill") at 2.93:1, under the 3:1
  // WCAG 1.4.11 non-text/UI-component minimum. `0xFFBF832C` was verified
  // at 3.23:1 — a ~5% luminance reduction along the same hue, not a
  // different color, chosen with headroom above the 3:1 floor rather
  // than the minimum value that technically clears it. ---
  static const Color warning50 = Color(0xFFFBF2E3);
  static const Color warning100 = Color(0xFFF5E1BD);
  static const Color warning300 = Color(0xFFE3B466);
  static const Color warning500 = Color(0xFFBF832C);
  static const Color warning700 = Color(0xFF95661F);
  static const Color warning900 = Color(0xFF5C3E12);

  // --- Danger — reserved for Safety Escalation and irreversible
  // destructive-action confirmation only (the Bible names both as the
  // narrow, deliberate exceptions to "no alarm-red overuse," Sections 10
  // and 18). A muted brick red, not a saturated alert red — it must still
  // read as serious without shouting on every screen it appears on. ---
  static const Color danger50 = Color(0xFFFBEAEA);
  static const Color danger100 = Color(0xFFF4CFCF);
  static const Color danger300 = Color(0xFFE0918F);
  static const Color danger500 = Color(0xFFC4443F);
  static const Color danger700 = Color(0xFF973330);
  static const Color danger900 = Color(0xFF5C1F1D);

  // --- Chart series — a small, ordered, qualitative set for distinguishing
  // simultaneous data series (e.g. push/pull/legs/core volume bars).
  // Reuses the semantic hues above rather than inventing a separate
  // "chart rainbow." The design system review flagged an earlier version
  // of this set (five colors, two of them — a muted teal and plum —
  // invented solely for charts, before a single chart component exists)
  // as speculative token creation: exactly the "guess at a shape before a
  // real need proves it" mistake this project's own TD-0001 history
  // already named as costly. Cut back to the three colors already
  // derived from the semantic palette; a real chart phase, with a real
  // chart needing a fourth or fifth series, is what should justify
  // inventing a new hue, not this phase guessing ahead of it.
  // `chartReference` is for guideline/threshold lines (e.g. a
  // training-load guardrail ceiling), which must read as structural, not
  // as another data series — hence neutral, not a hue. ---
  static const Color chart1 = signal500;
  static const Color chart2 = success500;
  static const Color chart3 = warning500;
  static const Color chartReference = neutral500;
}
