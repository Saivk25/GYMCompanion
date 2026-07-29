"""Tests for app/domain/user/enums.py.

`AccountStatus`'s values are pinned against a literal copy of
`app/infra/models.py`'s `_ACCOUNT_STATUSES` tuple rather than importing
that module directly: `tests/domain/` stays free of any infra/SQLAlchemy
dependency (see `pyproject.toml`'s `unit` marker — "fast, isolated tests
with no I/O — primarily app/domain"), and the AST import-boundary checker
only guards `app/domain` itself, not this directory, so nothing would stop
such an import except this deliberate convention. If this test and the
model's CHECK constraint ever drift apart, update both together.
"""

import pytest

from app.domain.user.enums import AccountStatus, BiologicalSex, ExperienceLevel

# Mirrors app/infra/models.py::_ACCOUNT_STATUSES exactly.
_INFRA_ACCOUNT_STATUSES = ("invited", "active", "suspended", "deleted", "purged")


@pytest.mark.unit
def test_account_status_values_match_the_infra_check_constraint() -> None:
    assert {member.value for member in AccountStatus} == set(_INFRA_ACCOUNT_STATUSES)


@pytest.mark.unit
def test_account_status_is_a_str_subclass() -> None:
    """Needed so a member serializes as its plain value (JSON, a database
    column, an event payload) rather than as `AccountStatus.ACTIVE`."""
    assert isinstance(AccountStatus.ACTIVE, str)
    assert AccountStatus.ACTIVE.value == "active"


@pytest.mark.unit
def test_experience_level_has_exactly_three_tiers() -> None:
    assert {member.value for member in ExperienceLevel} == {
        "beginner",
        "intermediate",
        "advanced",
    }


@pytest.mark.unit
def test_biological_sex_has_exactly_two_members() -> None:
    """Optionality is expressed by `UserProfile.sex` being
    `BiologicalSex | None` (see that class's docstring), not by a third
    member here."""
    assert {member.value for member in BiologicalSex} == {"female", "male"}
