"""Tests for app/domain/auth/enums.py."""

import pytest

from app.domain.auth.enums import ROLE_PERMISSIONS, Permission, Role


@pytest.mark.unit
def test_every_role_has_a_permissions_entry() -> None:
    for role in Role:
        assert role in ROLE_PERMISSIONS


@pytest.mark.unit
def test_member_role_grants_manage_own_data() -> None:
    assert Permission.MANAGE_OWN_DATA in ROLE_PERMISSIONS[Role.MEMBER]
