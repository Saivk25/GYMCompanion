# ADR 0013: Rule Engine foundation — one `RuleResult` shape at every level, code-defined `RuleId`, an empty `RuleContext`, and no `repository.py`

- Status: accepted
- Date: 2026-07-30

## Context

Sprint 3, Phase 1 asked for the "reusable Rule Engine infrastructure that
every future deterministic decision engine will use" — explicitly *not*
any fitness-specific logic. `backend/app/domain/rules/` needed `Rule`,
`RuleEngine`, `RuleContext`, `RuleResult`, `Recommendation`, and
`RecommendationSeverity`, with a `repository.py` only "if genuinely
needed."

The Domain Model & Decision Engine Bible grounds this package in two
places: Section 8.1's "Deterministic Rule Layer" ("applies hard gates and
guardrails first — contraindications, safety thresholds, volume ceilings.
Can block or constrain everything downstream; nothing downstream can
override it") and Section 10's nine named rule engines (Workout,
Nutrition, Recovery, Safety, Recommendation, Notification, Progress,
Analytics, AI Validation) — none of which are built yet. Because every one
of those nine will be built as a *consumer* of this package, every design
choice here is binding on all of them, which is why this ADR exists at
all (the task explicitly called this out: "document the Rule Engine
architecture because every future engine depends on it").

Four decisions needed to be made before writing code, each because the
task's own capability list left the concrete shape open:

1. **Is a single evaluated rule's result the same type as a whole
   engine's aggregated result?** The task lists `RuleResult`'s fields once
   ("passed/failed, severity, explanation, recommendations, triggered
   rules") and separately says `RuleEngine` "evaluates many rules,
   aggregates results" — it does not say whether "aggregates results"
   produces a *different* shape than what one `Rule` returns.

2. **What identifies a `Rule`?** The task says a Rule "has an id" but
   does not say whether that id is generated (like every aggregate's own
   `EntityId`, a UUID) or something else.

3. **What does `RuleContext` contain?** The task says a Rule "evaluates
   against a context" but gives no field list — unlike every aggregate
   built so far, which came with an explicit Rules/value-object list to
   work from.

4. **Is `repository.py` needed?** Explicitly conditional in the task
   ("only if genuinely needed").

## Decision

1. **`RuleResult` is one type used identically at both the single-`Rule`
   level and the `RuleEngine`-aggregate level.** `Rule.evaluate()` and
   `RuleEngine.evaluate()` both return a `RuleResult`, with the same field
   semantics at either level: `triggered_rules` is `(self.id,)` for one
   failed rule, or the union of every failed rule's id for an engine;
   `passed` is that one rule's outcome, or `True` only if every rule in
   the engine passed. A caller consuming an engine's output never needs a
   different type than a caller consuming one rule's output, and an
   engine's result could itself be fed into whatever future composition
   a higher-level engine needs, without a shape mismatch.

2. **`RuleId` is a plain, non-empty string value object — not a subclass
   of `app.domain.shared_kernel.EntityId`.** Every aggregate built so far
   uses `EntityId.generate()` (a random UUID) because instances are
   created at runtime and need a fresh identity each time. A `Rule` is
   the opposite: one fixed instance per concrete rule, defined once in
   code, and the Bible is explicit that "rule engines are versioned like
   code" and that a past `Decision` snapshot must remain explainable by
   referencing exactly which rule fired, even after the rule set changes
   (Section 12). A regenerated-per-process UUID could never serve as that
   stable, human-referenceable identity; a chosen slug
   (`"safety.contraindication_check"`) can. `RuleId` enforces no naming
   convention beyond non-emptiness — whichever concrete engine defines
   its own rules chooses its own naming scheme.

3. **`RuleContext` is an empty marker base class.** Each of the Bible's
   nine rule engines needs a completely different input snapshot; giving
   this shared base any field — even one as apparently universal as a
   timestamp for staleness/recency gating (Bible Section 8.4's confidence
   scoring, explicitly out of scope for this increment) — would mean
   inventing a shape every future engine is forced to inherit for a need
   this phase doesn't yet serve. `Rule` and `RuleEngine` are both generic
   over `RuleContext` subtypes (`Rule[TContext]`,
   `RuleEngine[TContext]`), so a concrete engine gets full static
   type-safety from its own context shape without this base class
   needing to define one.

4. **No `repository.py`.** A `Repository[TAggregate, TId]` (shared
   kernel) exists to let a domain-layer aggregate be looked up and saved
   without depending on `app.infra`. Rules are not aggregates: they are
   fixed, code-defined instances built by whichever concrete engine
   registers them with a `RuleEngine`, not created, mutated, or persisted
   through a repository. Building one here would be speculative
   infrastructure for a need nothing in this codebase has yet.

Two smaller, colocated decisions worth recording:

- **Severity is ranked explicitly (`severity_rank()`), never by `Enum`
  declaration order or by relying on `RecommendationSeverity`'s `str`
  mixin.** `RecommendationSeverity` follows the same `(str, Enum)`
  convention as every enum in this codebase, but `str.__lt__` would
  compare members lexicographically ("critical" < "warning"), the wrong
  ordering for a severity scale — `severity_rank()` is the single,
  explicit source of truth `engine.py`'s aggregation logic uses.
- **A `Rule`'s `severity` is fixed per instance, not computed per
  evaluation**, and is stamped onto every `RuleResult` it produces
  (passed or failed) via the `_pass()`/`_fail()` helper methods `Rule`
  provides — a rule checking something safety-critical is always
  `CRITICAL`, never conditionally `WARNING` depending on the input.

## Consequences

Every future concrete rule engine (Workout Rules, Safety Rules, and the
rest of the Bible's nine) is expected to be built as *an instance of*
`RuleEngine[TheirContext]`, configured with their own `Rule[TheirContext]`
subclasses and their own `TheirContext(RuleContext)` — not as a subclass
overriding `RuleEngine`'s behavior. `RuleEngine` itself should stay this
thin; if a future engine needs behavior `RuleEngine` doesn't provide
(short-circuiting on the first `CRITICAL` failure, say), that is new,
deliberate scope for that increment's own ADR, not something to bolt onto
this shared class silently.

Because `RuleId` carries no generation mechanism, whichever engine
defines the first real rules is also responsible for establishing this
codebase's actual naming convention (a dotted namespace, matching this
ADR's own examples, is the natural choice, but nothing here enforces it).

Because `RuleContext` has no fields, every future engine's context class
starts from zero — there is no shared "given" data (user id, evaluation
timestamp) a rule can assume is present without its specific context
type declaring it. This is a deliberate rejection of premature
abstraction, not an oversight; Section 8.4's confidence-scoring and
recency-gating needs, if and when built, are the more natural place to
decide whether they belong on every context or only some.
