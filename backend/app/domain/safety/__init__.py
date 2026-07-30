"""The Safety bounded context (Domain Model & Decision Engine Bible,
Section 3, Table 2: "Recovery & Safety").

Unlike every other top-level package under `app.domain`, this one holds
no aggregate of its own yet — the Bible's `SafetyFlag`/`EscalationCase`
entities (Section 5's catalog) are not built here, the same reasoning
`app.domain.user.value_objects.UserProfile`'s own docstring already gives
for omitting `injury_flags` rather than adding a placeholder. Only
`app.domain.safety.rules` exists: Sprint 3, Phase 6's Safety Rule Engine,
which evaluates safety from data supplied by *other* already-built
contexts (`Readiness`, Progressive Overload) plus two small, new value
objects for restriction/injury data no existing aggregate carries yet
— see `app.domain.safety.rules`'s own docstring and
`docs/adr/0018-safety-rule-engine-composition-and-authority.md`.
"""
