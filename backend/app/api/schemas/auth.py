"""Request/response schemas for the Authentication endpoints
(`app/api/routes/auth.py`). See `common.py`'s module docstring for the
value-object <-> primitive conversion convention every other schema
module follows — the one deliberate departure here is `password`,
which stays a plain `str` all the way into the `Command` itself. See
`app.application.auth.commands.register.RegisterCommand`'s own
docstring for why: a `PasswordHash` can only be produced by hashing,
and hashing happens inside the Authentication Application Layer, never
here.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.application.auth.commands.login import LoginCommand
from app.application.auth.commands.refresh import RefreshCommand
from app.application.auth.commands.register import RegisterCommand
from app.application.auth.dto.auth_tokens_dto import AuthTokensDTO
from app.application.auth.dto.current_user_dto import CurrentUserDTO
from app.domain.auth.enums import Role
from app.domain.auth.value_objects import Email
from app.domain.user.enums import AccountStatus
from app.domain.user.value_objects import Locale, Timezone


class RegisterRequest(BaseModel):
    email: str
    password: str
    locale: str
    timezone: str

    def to_command(self) -> RegisterCommand:
        return RegisterCommand(
            email=Email(self.email),
            password=self.password,
            locale=Locale(self.locale),
            timezone=Timezone(self.timezone),
        )


class LoginRequest(BaseModel):
    email: str
    password: str

    def to_command(self) -> LoginCommand:
        return LoginCommand(email=Email(self.email), password=self.password)


class RefreshRequest(BaseModel):
    refresh_token: str

    def to_command(self) -> RefreshCommand:
        return RefreshCommand(refresh_token=self.refresh_token)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int = Field(description="Access token lifetime, in seconds.")

    @classmethod
    def from_dto(cls, dto: AuthTokensDTO) -> TokenResponse:
        return cls(
            access_token=dto.access_token,
            refresh_token=dto.refresh_token,
            token_type=dto.token_type,
            expires_in=dto.expires_in,
        )


class CurrentUserResponse(BaseModel):
    user_id: str
    email: str
    role: Role
    account_status: AccountStatus
    locale: str
    timezone: str
    created_at: str = Field(description="ISO-8601 timestamp.")

    @classmethod
    def from_dto(cls, dto: CurrentUserDTO) -> CurrentUserResponse:
        return cls(
            user_id=str(dto.user_id),
            email=dto.email.value,
            role=dto.role,
            account_status=dto.account_status,
            locale=dto.locale.value,
            timezone=dto.timezone.value,
            created_at=dto.created_at.isoformat(),
        )
