"""SQLAlchemy ORM models: the persistence shape of each aggregate.

Split one file per aggregate (mirroring `app/domain`'s own per-aggregate
package layout) now that every tenant-scoped aggregate has a table —
`app/infra/models.py` (a single file) was adequate for `UserAccount`
alone; it is not for ten. Re-exported here so `from app.infra.models
import X` keeps working exactly as it did as a single module — no caller
outside this package needs to know it is now a package.

These are infra-layer mapping classes, not the Domain Core — see
`app/infra/orm_base.py`'s module docstring for the framework-boundary
rule these classes live on the allowed side of. Repositories
(`app/infra/repositories/`) translate between a row here and the
matching framework-free aggregate in `app/domain`; nothing in this
package is ever imported by `app/domain`.
"""

from app.infra.models.exercise import ExerciseRow
from app.infra.models.goal import GoalRow
from app.infra.models.nutrition import NutritionRow
from app.infra.models.progress import ProgressRow
from app.infra.models.readiness import ReadinessRow
from app.infra.models.user import UserAccount
from app.infra.models.workout import WorkoutRow
from app.infra.models.workout_session import (
    ExercisePerformanceRow,
    ExerciseSetRow,
    WorkoutSessionRow,
)

__all__ = [
    "ExercisePerformanceRow",
    "ExerciseRow",
    "ExerciseSetRow",
    "GoalRow",
    "NutritionRow",
    "ProgressRow",
    "ReadinessRow",
    "UserAccount",
    "WorkoutRow",
    "WorkoutSessionRow",
]
