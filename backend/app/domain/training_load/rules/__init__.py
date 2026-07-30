"""The Training Load Rule Engine: Sprint 3 Phase 8's sixth concrete
deterministic rule engine, built on the Phase 1 Rule Engine foundation
(`app.domain.rules`) and, like Safety before it, holding no aggregate
of its own — see the parent `app.domain.training_load` package's
docstring for why.

This engine evaluates accumulated training load from historical
summaries the *application layer* prepares, and produces deterministic
`Recommendation`s alone — no AI, no exercise recommendation, no
workout planning.

Five independent rules (`AcuteLoadRule`, `ChronicLoadRule`,
`LoadRatioRule`, `MonotonyRule`, `StrainRule`), composed by
`TrainingLoadRuleEngine` (itself a thin, behavior-preserving
configuration of the shared `RuleEngine[TrainingLoadRuleContext]`).
Missing or insufficient history passes with an explanation rather than
failing, the same convention every prior engine in this codebase
follows — see each rule's own docstring for what "insufficient" means
for it specifically. See
`docs/adr/0020-training-load-supplied-summaries.md` for the
architectural decisions specific to this package: why
`TrainingLoadRuleContext` builds no summaries of its own (unlike
Progressive Overload), how deterministic load evaluation stays
side-effect free with no wall-clock reads, and how this engine's rules
are deliberately independent from Progressive Overload's and Safety's
own load-adjacent rules rather than duplicates of either.

Depends on nothing outside the Python standard library and
`app.domain.shared_kernel`/`app.domain.rules` (the Phase 1 foundation)
— enforced by the same statically-checked rule as the rest of
`app/domain` (`tests/domain/test_import_boundaries.py`).

No `repository.py` in this package, the same reasoning
`app.domain.rules.__init__`'s own docstring documents: this engine
consumes context objects, never loads its own data.
"""

from app.domain.training_load.rules.acute_load_rule import AcuteLoadRule
from app.domain.training_load.rules.chronic_load_rule import ChronicLoadRule
from app.domain.training_load.rules.context import (
    TrainingLoad,
    TrainingLoadDate,
    TrainingLoadRuleContext,
    TrainingLoadSummary,
)
from app.domain.training_load.rules.load_ratio_rule import LoadRatioRule
from app.domain.training_load.rules.monotony_rule import MonotonyRule
from app.domain.training_load.rules.strain_rule import StrainRule
from app.domain.training_load.rules.training_load_rule_engine import TrainingLoadRuleEngine

__all__ = [
    "AcuteLoadRule",
    "ChronicLoadRule",
    "LoadRatioRule",
    "MonotonyRule",
    "StrainRule",
    "TrainingLoad",
    "TrainingLoadDate",
    "TrainingLoadRuleContext",
    "TrainingLoadRuleEngine",
    "TrainingLoadSummary",
]
