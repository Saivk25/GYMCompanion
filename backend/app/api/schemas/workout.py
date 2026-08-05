"""Request/response schemas for the Workout and WorkoutSession endpoints
(`app/api/routes/v1/workout.py`). See `goal.py`'s module docstring for
the conventions this file follows (no duplicated range validation;
`None` means whatever the corresponding command already documents it to
mean).

Two aggregates, one file: `WorkoutSession` (and its child entity
`ExercisePerformance`) has no query handler of its own separate from
`Workout`'s module in the Application Layer's own `dto/` package
(`workout_dto.py` and `workout_session_dto.py` sit side by side), so
this schema file mirrors that pairing rather than splitting into a
`workout_session.py` the Application Layer itself doesn't have a
counterpart for.

`UpdateWorkoutRequest` is a full replacement, not a partial patch —
matching `UpdateWorkoutCommand`'s own documented semantics exactly
(`app.application.workout.commands.update_workout`): a field of `None`
here *clears* that field, it does not "leave it unchanged". This is the
opposite convention from Nutrition's `UpdateNutritionRequest` — each
schema mirrors whatever its own command already means by `None`, never
inventing a uniform rule across modules.

`ExerciseSet` (`app.domain.workout_session.exercise_set`) is the one
value object in this codebase that is *not* a single-primitive `.value`
wrapper — it has four fields (`set_number`, `weight`, `reps`, `rpe`) plus
a plain `bool` — so `ExercisePerformanceResponse` unwraps each field
individually rather than using `common.unwrap()`.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.api.schemas.common import duration_to_seconds, seconds_to_duration, unwrap, unwrap_optional
from app.application.workout.commands.complete_exercise_set import CompleteExerciseSetCommand
from app.application.workout.commands.complete_workout_session import (
    CompleteWorkoutSessionCommand,
)
from app.application.workout.commands.create_workout import CreateWorkoutCommand
from app.application.workout.commands.log_exercise_set import LogExerciseSetCommand
from app.application.workout.commands.start_workout_session import StartWorkoutSessionCommand
from app.application.workout.commands.update_workout import UpdateWorkoutCommand
from app.application.workout.dto.workout_dto import WorkoutDTO
from app.application.workout.dto.workout_session_dto import (
    ExercisePerformanceDTO,
    WorkoutSessionDTO,
)
from app.domain.exercise.identifiers import ExerciseId
from app.domain.user.identifiers import UserId
from app.domain.workout.identifiers import WorkoutId
from app.domain.workout.value_objects import WorkoutDate, WorkoutGoal, WorkoutName, WorkoutNotes
from app.domain.workout_session.exercise_set import SetNumber, SetReps, SetRPE, SetWeight
from app.domain.workout_session.identifiers import ExercisePerformanceId, WorkoutSessionId
from app.domain.workout_session.value_objects import (
    CompletionPercentage,
    SessionDate,
    SessionDuration,
    SessionRating,
)

# ---------------------------------------------------------------------------
# Workout
# ---------------------------------------------------------------------------


class CreateWorkoutRequest(BaseModel):
    """No `user_id` field — see `app.api.schemas.goal.CreateGoalRequest`'s
    identical docstring for why."""

    name: str
    planned_date: date
    goal: str | None = None
    notes: str | None = None

    def to_command(self, user_id: UserId) -> CreateWorkoutCommand:
        return CreateWorkoutCommand(
            user_id=user_id,
            name=WorkoutName(self.name),
            planned_date=WorkoutDate(self.planned_date),
            goal=WorkoutGoal(self.goal) if self.goal is not None else None,
            notes=WorkoutNotes(self.notes) if self.notes is not None else None,
        )


class UpdateWorkoutRequest(BaseModel):
    """A field left `None` *clears* it — see the module docstring."""

    goal: str | None = None
    notes: str | None = None

    def to_command(self, workout_id: WorkoutId, requester_id: UserId) -> UpdateWorkoutCommand:
        return UpdateWorkoutCommand(
            workout_id=workout_id,
            requester_id=requester_id,
            goal=WorkoutGoal(self.goal) if self.goal is not None else None,
            notes=WorkoutNotes(self.notes) if self.notes is not None else None,
        )


class WorkoutResponse(BaseModel):
    workout_id: str
    user_id: str
    status: str
    name: str
    planned_date: date
    planned_at: str
    goal: str | None
    notes: str | None
    duration_seconds: float | None
    started_at: str | None
    completed_at: str | None
    cancelled_at: str | None

    @classmethod
    def from_dto(cls, dto: WorkoutDTO) -> WorkoutResponse:
        return cls(
            workout_id=str(dto.workout_id),
            user_id=str(dto.user_id),
            status=dto.status.value,
            name=unwrap(dto.name),
            planned_date=unwrap(dto.planned_date),
            planned_at=dto.planned_at.isoformat(),
            goal=unwrap_optional(dto.goal),
            notes=unwrap_optional(dto.notes),
            duration_seconds=(
                duration_to_seconds(dto.duration.value) if dto.duration is not None else None
            ),
            started_at=dto.started_at.isoformat() if dto.started_at is not None else None,
            completed_at=dto.completed_at.isoformat() if dto.completed_at is not None else None,
            cancelled_at=dto.cancelled_at.isoformat() if dto.cancelled_at is not None else None,
        )


# CancelWorkoutCommand takes only a WorkoutId — no request body schema of
# its own is needed; the route constructs `CancelWorkoutCommand(workout_id=...)`
# directly, the same "no superfluous wrapper" call goal.py's own module
# docstring makes for CompleteGoalCommand/CancelGoalCommand.


# ---------------------------------------------------------------------------
# WorkoutSession
# ---------------------------------------------------------------------------


class StartWorkoutSessionRequest(BaseModel):
    session_date: date

    def to_command(self, workout_id: WorkoutId, requester_id: UserId) -> StartWorkoutSessionCommand:
        return StartWorkoutSessionCommand(
            workout_id=workout_id,
            requester_id=requester_id,
            session_date=SessionDate(self.session_date),
        )


class CompleteWorkoutSessionRequest(BaseModel):
    duration_seconds: float
    completion_percentage: float
    rating: int | None = None

    def to_command(
        self, session_id: WorkoutSessionId, requester_id: UserId
    ) -> CompleteWorkoutSessionCommand:
        return CompleteWorkoutSessionCommand(
            session_id=session_id,
            requester_id=requester_id,
            duration=SessionDuration(seconds_to_duration(self.duration_seconds)),
            completion_percentage=CompletionPercentage(self.completion_percentage),
            rating=SessionRating(self.rating) if self.rating is not None else None,
        )


class LogExerciseSetRequest(BaseModel):
    exercise_id: str
    set_number: int
    weight: float
    reps: int
    rpe: int

    def to_command(
        self, session_id: WorkoutSessionId, requester_id: UserId
    ) -> LogExerciseSetCommand:
        return LogExerciseSetCommand(
            session_id=session_id,
            requester_id=requester_id,
            exercise_id=ExerciseId.parse(self.exercise_id),
            set_number=SetNumber(self.set_number),
            weight=SetWeight(self.weight),
            reps=SetReps(self.reps),
            rpe=SetRPE(self.rpe),
        )


class CompleteExerciseSetRequest(BaseModel):
    performance_id: str
    set_number: int

    def to_command(
        self, session_id: WorkoutSessionId, requester_id: UserId
    ) -> CompleteExerciseSetCommand:
        return CompleteExerciseSetCommand(
            session_id=session_id,
            requester_id=requester_id,
            performance_id=ExercisePerformanceId.parse(self.performance_id),
            set_number=self.set_number,
        )


class ExerciseSetResponse(BaseModel):
    set_number: int
    weight: float
    reps: int
    rpe: int
    completed: bool


class ExercisePerformanceResponse(BaseModel):
    performance_id: str
    exercise_id: str
    notes: str
    sets: list[ExerciseSetResponse]

    @classmethod
    def from_dto(cls, dto: ExercisePerformanceDTO) -> ExercisePerformanceResponse:
        return cls(
            performance_id=str(dto.performance_id),
            exercise_id=str(dto.exercise_id),
            notes=unwrap(dto.notes),
            sets=[
                ExerciseSetResponse(
                    set_number=unwrap(exercise_set.set_number),
                    weight=unwrap(exercise_set.weight),
                    reps=unwrap(exercise_set.reps),
                    rpe=unwrap(exercise_set.rpe),
                    completed=exercise_set.completed,
                )
                for exercise_set in dto.sets
            ],
        )


class WorkoutSessionResponse(BaseModel):
    session_id: str
    workout_id: str
    user_id: str
    status: str
    session_date: date
    planned_at: str
    notes: str
    duration_seconds: float | None
    completion_percentage: float | None
    rating: int | None
    started_at: str | None
    completed_at: str | None
    abandoned_at: str | None
    exercise_performances: list[ExercisePerformanceResponse]

    @classmethod
    def from_dto(cls, dto: WorkoutSessionDTO) -> WorkoutSessionResponse:
        return cls(
            session_id=str(dto.session_id),
            workout_id=str(dto.workout_id),
            user_id=str(dto.user_id),
            status=dto.status.value,
            session_date=unwrap(dto.session_date),
            planned_at=dto.planned_at.isoformat(),
            notes=unwrap(dto.notes),
            duration_seconds=(
                duration_to_seconds(dto.duration.value) if dto.duration is not None else None
            ),
            completion_percentage=unwrap_optional(dto.completion_percentage),
            rating=unwrap_optional(dto.rating),
            started_at=dto.started_at.isoformat() if dto.started_at is not None else None,
            completed_at=dto.completed_at.isoformat() if dto.completed_at is not None else None,
            abandoned_at=dto.abandoned_at.isoformat() if dto.abandoned_at is not None else None,
            exercise_performances=[
                ExercisePerformanceResponse.from_dto(performance)
                for performance in dto.exercise_performances
            ],
        )
