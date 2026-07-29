# ADR 0003: Riverpod for state management, no code generation in the MVP scaffold

- Status: accepted
- Date: 2026-07-29

## Context

None of the six frozen documents pin a Flutter state-management library — the
Engineering Master Plan names `go_router` (routing) and `Drift` (local persistence)
explicitly but leaves this choice open. A choice is needed now to write real screens
starting Sprint 2.

## Decision

`flutter_riverpod`, using plain hand-written providers (`Provider`, `StateNotifierProvider`,
or the classic `Notifier` API) rather than `riverpod_generator`/`freezed` code generation.

Reasoning:

- Riverpod is boring, mature, and widely documented — consistent with the Engineering
  Master Plan's "boring technology by default" principle (Section 1).
- It is straightforward to unit-test providers in isolation without a widget tree,
  which matters given the Engineering Master Plan's testing standards (Section 9).
- Explicitly avoiding code generation for this scaffold removes a `build_runner` step
  from the toolchain while the implementation sandbox cannot run one to verify it
  works (ADR 0002). This can be revisited once development moves to a machine with a
  full Flutter toolchain, if a feature's complexity genuinely justifies it — not
  before.

## Consequences

Every provider in this codebase is hand-written and directly readable without a
generated `.g.dart` counterpart. If a future feature's state shape becomes complex
enough that this becomes painful, that pain is the justification needed to introduce
code generation — matching the Engineering Master Plan's instruction to delay
optimization until it's justified rather than adopted speculatively.
