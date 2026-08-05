"""Tests for app/application/auth/dto/current_user_dto.py."""

import pytest

from app.application.auth.dto.current_user_dto import CurrentUserDTO
from app.domain.auth.enums import Role
from app.domain.user.enums import AccountStatus
from app.domain.user.identifiers import UserId
from tests.application.auth.factories import a_registered_credential, a_registered_user


@pytest.mark.unit
def test_from_user_and_credential_combines_both_aggregates() -> None:
    user_id = UserId.generate()
    user = a_registered_user(user_id=user_id)
    credential = a_registered_credential(user_id=user_id)

    dto = CurrentUserDTO.from_user_and_credential(user, credential)

    assert dto.user_id == user_id
    assert dto.email == credential.email
    assert dto.role == Role.MEMBER
    assert dto.account_status == AccountStatus.INVITED
    assert dto.locale == user.locale
    assert dto.timezone == user.timezone
    assert dto.created_at == user.created_at
