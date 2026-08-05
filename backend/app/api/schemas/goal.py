"""Request/response schemas for the Goal endpoints
(`app/api/routes/v1/goal.py`). See `common.py`'s module docstring for
the value-object <-> primitive conversion convention every method here
follows — request schemas build domain value objects via `to_command()`,
response schemas unwrap them via `from_dto()`.

No range/length validation is duplicated here (e.g. "priority must be
1-5") — every such rule is already enforced once, by the corresponding
value object's own `__post_init__` (`app.domain.goal.value_objects`),
raising `DomainInvariantViolationError` on invalid input, which
`app/api/errors.py` maps to a 422 response. Re-checking the same bound
in a Pydantic `Field(ge=1, le=5)` here would be a second, driftable copy
of a business rule the API Layer must not own — see this phase's own
rule, "No business logic."
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.api.schemas.common import unwrap, unwrap_optional
from app.application.goal.commands.create_goal import CreateGoalCommand
from app.application.goal.commands.update_goal import UpdateGoalCommand
from app.application.goal.dto.goal_dto import GoalDTO
from app.domain.goal.enums import GoalStatus, GoalType
from app.domain.goal.identifiers import GoalId
from app.domain.goal.value_objects import (
    GoalDescription,
    GoalName,
    GoalNotes,
    Priority,
    TargetBodyFat,
    TargetDate,
    TargetStrength,
    TargetWeight,
)
from app.domain.user.identifiers import UserId


class CreateGoalRequest(BaseModel):
    """No `user_id` field — the owner of a created Goal is always the
    authenticated caller (`app.api.deps.get_current_user_id`), never a
    value the client supplies. See `docs/adr/0032-authentication-and-
    authorization.md`."""

    goal_type: GoalType
    name: str
    target_date: date
    description: str | None = None
    target_weight: float | None = None
    target_body_fat: float | None = None
    target_strength: float | None = None
    priority: int | None = None
    notes: str | None = None

    def to_command(self, user_id: UserId) -> CreateGoalCommand:
        return CreateGoalCommand(
            user_id=user_id,
            goal_type=self.goal_type,
            name=GoalName(self.name),
            target_date=TargetDate(self.target_date),
            description=(
                GoalDescription(self.description) if self.description is not None else None
            ),
            target_weight=(
                TargetWeight(self.target_weight) if self.target_weight is not None else None
            ),
            target_body_fat=(
                TargetBodyFat(self.target_body_fat) if self.target_body_fat is not None else None
            ),
            target_strength=(
                TargetStrength(self.target_strength) if self.target_strength is not None else None
            ),
            priority=Priority(self.priority) if self.priority is not None else None,
            notes=GoalNotes(self.notes) if self.notes is not None else None,
        )


class UpdateGoalRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    target_date: date | None = None
    target_weight: float | None = None
    target_body_fat: float | None = None
    target_strength: float | None = None
    priority: int | None = None
    notes: str | None = None

    def to_command(self, goal_id: GoalId) -> UpdateGoalCommand:
        return UpdateGoalCommand(
            goal_id=goal_id,
            name=GoalName(self.name) if self.name is not None else None,
            description=(
                GoalDescription(self.description) if self.description is not None else None
            ),
            target_date=TargetDate(self.target_date) if self.target_date is not None else None,
            target_weight=(
                TargetWeight(self.target_weight) if self.target_weight is not None else None
            ),
            target_body_fat=(
                TargetBodyFat(self.target_body_fat) if self.target_body_fat is not None else None
            ),
            target_strength=(
                TargetStrength(self.target_strength) if self.target_strength is not None else None
            ),
            priority=Priority(self.priority) if self.priority is not None else None,
            notes=GoalNotes(self.notes) if self.notes is not None else None,
        )


class GoalResponse(BaseModel):
    goal_id: str
    user_id: str
    goal_type: GoalType
    name: str
    target_date: date
    created_at: str = Field(description="ISO-8601 timestamp.")
    description: str | None
    target_weight: float | None
    target_body_fat: float | None
    target_strength: float | None
    priority: int | None
    notes: str
    status: GoalStatus
    updated_at: str | None
    completed_at: str | None
    cancelled_at: str | None

    @classmethod
    def from_dto(cls, dto: GoalDTO) -> GoalResponse:
        return cls(
            goal_id=str(dto.goal_id),
            user_id=str(dto.user_id),
            goal_type=dto.goal_type,
            name=unwrap(dto.name),
            target_date=unwrap(dto.target_date),
            created_at=dto.created_at.isoformat(),
            description=unwrap_optional(dto.description),
            target_weight=unwrap_optional(dto.target_weight),
            target_body_fat=unwrap_optional(dto.target_body_fat),
            target_strength=unwrap_optional(dto.target_strength),
            priority=unwrap_optional(dto.priority),
            notes=unwrap(dto.notes),
            status=dto.status,
            updated_at=dto.updated_at.isoformat() if dto.updated_at is not None else None,
            completed_at=dto.completed_at.isoformat() if dto.completed_at is not None else None,
            cancelled_at=dto.cancelled_at.isoformat() if dto.cancelled_at is not None else None,
        )
