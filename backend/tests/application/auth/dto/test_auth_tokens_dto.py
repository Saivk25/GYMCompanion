"""Tests for app/application/auth/dto/auth_tokens_dto.py."""

import pytest

from app.application.auth.dto.auth_tokens_dto import AuthTokensDTO


@pytest.mark.unit
def test_defaults_token_type_to_bearer() -> None:
    dto = AuthTokensDTO(access_token="a", refresh_token="r", expires_in=900)
    assert dto.token_type == "bearer"


@pytest.mark.unit
def test_carries_the_fields_it_was_given() -> None:
    dto = AuthTokensDTO(access_token="a", refresh_token="r", expires_in=900)
    assert dto.access_token == "a"
    assert dto.refresh_token == "r"
    assert dto.expires_in == 900
