"""`TrainingLoadRuleEngine`: composes the five training load rules into
one `RuleEngine[TrainingLoadRuleContext]`, the "configuration-only
subclass" pattern every concrete rule engine in this codebase follows
(`docs/adr/0013-rule-engine-foundation.md`).
"""

from __future__ import annotations

from collections.abc import Sequence

from app.domain.rules.engine import RuleEngine
from app.domain.rules.rule import Rule
from app.domain.training_load.rules.acute_load_rule import AcuteLoadRule
from app.domain.training_load.rules.chronic_load_rule import ChronicLoadRule
from app.domain.training_load.rules.context import TrainingLoadRuleContext
from app.domain.training_load.rules.load_ratio_rule import LoadRatioRule
from app.domain.training_load.rules.monotony_rule import MonotonyRule
from app.domain.training_load.rules.strain_rule import StrainRule


def _default_rules() -> tuple[Rule[TrainingLoadRuleContext], ...]:
    return (AcuteLoadRule(), ChronicLoadRule(), LoadRatioRule(), MonotonyRule(), StrainRule())


class TrainingLoadRuleEngine(RuleEngine[TrainingLoadRuleContext]):
    """Evaluation-only: computes findings about accumulated training
    load from supplied summaries. It cannot itself block a session or
    override another engine's output — the same evaluation-only
    authority `SafetyRuleEngine` documents for itself
    (`docs/adr/0018-safety-rule-engine-composition-and-authority.md`).
    """

    def __init__(self, rules: Sequence[Rule[TrainingLoadRuleContext]] | None = None) -> None:
        super().__init__(rules if rules is not None else _default_rules())
