# ADR 0005: User aggregate, first increment — scope and two naming decisions

- Status: accepted
- Date: 2026-07-29

## Context

Sprint 2 begins with the first real aggregate, `User` (Domain Model & Decision
Engine Bible, Section 4.1). The task scope named five things to include —
`UserId`, `User`, `UserProfile` value objects, `UserPreferences`, `UserContext` —
alongside `UserRegistered`/`UserProfileUpdated` events and a repository
interface. Two of those five names do not map onto the Bible one-to-one, and
implementing them literally without a documented decision would either
silently under-build a Bible aggregate or silently invent a Bible concept
that doesn't exist. Both needed a call before writing code, not after.

## Decision

**1. `UserProfile` is a value object nested in `User`, not the Bible's
standalone `Profile` aggregate (Section 4.2).**

The Bible's `Profile` is a full aggregate: its own identity, its own
Draft -> Complete -> Stale -> Complete lifecycle, and independent versioning
against `AIInferenceRecord` snapshots so past recommendations stay
explainable after a profile edit. Building that in full now would be
speculative — nothing in this codebase yet reads a Profile edit
independently of the User that owns it; the versioning-for-explainability
need only exists once `AIInferenceRecord` and real recommendations exist.

Instead, `app/domain/user/value_objects.py`'s `UserProfile` is an immutable
value object: `height_cm`, `birth_year`, `experience_level`, `sex` (optional),
replaced wholesale on every edit via `User.update_profile(...)`. Because a
`ValueObject` is either fully valid or doesn't exist, `User.has_complete_profile`
is exactly `profile is not None` — the Bible's Draft/Complete distinction
falls out for free, without a separate state machine. "Stale" (a fact that
hasn't been reconfirmed in N months) is not modeled: it needs a `Clock`-driven
staleness check this increment has no use for yet. `injury_flags` and
`dietary_pattern` — also key attributes of `Profile` in the Bible — are
omitted rather than stubbed, since they're references to `SafetyFlag` and
`NutritionPattern`, neither of which exists yet.

**2. `UserContext` is a new, unrelated concept — not the Bible's
`EnvironmentContext`.**

The Bible already uses "Context" for a specific aggregate: `EnvironmentContext`
(Section 4.3, Table 6), bundling a location, an equipment set, and a
food-environment tag — a User has many, exactly one Active. The task's
`UserContext` is a different shape entirely: an immutable snapshot of a
single `User` (id, account status, locale, timezone, profile, preferences)
for a future domain service to consume without depending on the mutable
aggregate or a live repository mid-calculation. `app/domain/user/context.py`
implements it as exactly that — carrying no location/equipment/food data,
never persisted, no lifecycle — and documents the naming collision explicitly
in its module docstring so a future reader doesn't conflate the two.

## Consequences

Promoting `UserProfile` to a standalone aggregate later is a real migration,
not a free rename: it needs its own `ProfileId`, its own repository, and a
decision about how `User` references it (an id, most likely, per the Bible's
1:1 relationship). That migration is deferred until a second real consumer
of profile history — most plausibly `AIInferenceRecord` snapshotting — makes
the current value-object shape genuinely insufficient, not before.

`UserContext`'s name collision with the Bible's "Context" is a known,
accepted rough edge, not a mistake to silently work around. If it causes
real confusion once rule engines are built and both concepts are in active
use side by side, renaming `UserContext` is a single-file, mechanical change
(nothing else in the domain depends on it yet) — the Bible's own
`EnvironmentContext` is not renamed to accommodate it.

Two domain events were considered and rejected for this increment:
`UserActivated`/`UserSuspended`/`UserDeleted`/`AccountPurged`-style events for
the rest of `User`'s state machine, and `UserPreferencesUpdated`. Neither has
a real subscriber yet (Notification & Automation, AI Governance's purge
cascade — none built). Each is added when its first real consumer is, per
the Engineering Master Plan's "boring technology" principle — not
speculatively ahead of that, matching how `docs/adr/0002` and `docs/adr/0004`
already deferred verification/tooling that had no present justification.
