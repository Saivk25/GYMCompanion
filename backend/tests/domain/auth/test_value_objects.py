"""Tests for app/domain/auth/value_objects.py."""

import pytest

from app.domain.auth.value_objects import Email, PasswordHash
from app.domain.shared_kernel.errors import DomainInvariantViolationError

# --- Email ---


@pytest.mark.unit
def test_email_accepts_a_plausible_address() -> None:
    assert Email("sai@example.com").value == "sai@example.com"


@pytest.mark.unit
def test_email_normalizes_case_and_whitespace() -> None:
    assert Email("  Sai@Example.COM  ").value == "sai@example.com"


@pytest.mark.unit
def test_two_emails_differing_only_by_case_are_equal() -> None:
    assert Email("Sai@Example.com") == Email("sai@example.com")


@pytest.mark.unit
@pytest.mark.parametrize(
    "raw",
    ["", "   ", "not-an-email", "missing-domain@", "@missing-local.com", "no-at-sign.com"],
)
def test_email_rejects_implausible_input(raw: str) -> None:
    with pytest.raises(DomainInvariantViolationError):
        Email(raw)


# --- PasswordHash ---


@pytest.mark.unit
def test_password_hash_accepts_a_non_empty_opaque_string() -> None:
    assert PasswordHash("$2b$12$abcdefghijklmnopqrstuv").value == "$2b$12$abcdefghijklmnopqrstuv"


@pytest.mark.unit
@pytest.mark.parametrize("raw", ["", "   "])
def test_password_hash_rejects_empty_input(raw: str) -> None:
    with pytest.raises(DomainInvariantViolationError):
        PasswordHash(raw)
