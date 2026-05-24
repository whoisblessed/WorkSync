from pydantic import BaseModel, EmailStr

from app.models.user import Role


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Tokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: EmailStr
    role: Role


class RefreshTokenRequest(BaseModel):
    refresh_token: str
