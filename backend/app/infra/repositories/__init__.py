"""SQLAlchemy-backed implementations of every aggregate's `Repository`
interface (`app.domain.*.repository`) — the Persistence Layer's public
surface (Engineering Master Plan, Section 3.2: "One repository class per
aggregate root, hiding SQLAlchemy from every caller outside infra/").

Every class here takes a `sqlalchemy.orm.Session` and nothing else; there is
no concrete `UnitOfWork` yet to construct these for a caller (see
`app/application/shared/unit_of_work.py`'s own docstring — that wiring is
explicitly a future phase's scope, not this one). See
`_tracking.py`'s module docstring for the shared mechanism that makes
`repository.get(id)`, mutate, then a later `session.commit()` actually
persist the mutation with no second `add()` call — the exact shape every
handler in `app/application/*/handlers` already uses.
"""

from app.infra.repositories.exercise_repository import ExerciseSqlRepository
from app.infra.repositories.goal_repository import GoalSqlRepository
from app.infra.repositories.nutrition_repository import NutritionSqlRepository
from app.infra.repositories.progress_repository import ProgressSqlRepository
from app.infra.repositories.readiness_repository import ReadinessSqlRepository
from app.infra.repositories.user_repository import UserSqlRepository
from app.infra.repositories.workout_repository import WorkoutSqlRepository
from app.infra.repositories.workout_session_repository import WorkoutSessionSqlRepository

__all__ = [
    "ExerciseSqlRepository",
    "GoalSqlRepository",
    "NutritionSqlRepository",
    "ProgressSqlRepository",
    "ReadinessSqlRepository",
    "UserSqlRepository",
    "WorkoutSessionSqlRepository",
    "WorkoutSqlRepository",
]
