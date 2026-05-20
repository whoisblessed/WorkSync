from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
import jwt

from app.core.config import settings


# Пароли

pwd_context = CryptContext(["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Преобразует пароль в хеш с использованием bcrypt"""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, соответствует ли введённый пароль сохранtнному хешу"""
    return pwd_context.verify(plain_password, hashed_password)


# JWT


def create_access_token(data: dict) -> str:
    """Создает access JWT"""

    payload = data.copy()
    payload.update(
        {
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=settings.jwt.access_token_expire_minutes),
            "type": "access",
        }
    )

    return jwt.encode(payload, settings.jwt.secret_key, settings.jwt.algorithm)


def create_refresh_token(data: dict) -> str:
    """Создает refresh JWT"""

    payload = data.copy()
    payload.update(
        {
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc)
            + timedelta(days=settings.jwt.refresh_token_expire_days),
            "type": "refresh",
        }
    )

    return jwt.encode(payload, settings.jwt.secret_key, settings.jwt.algorithm)


def decode_token(token: str) -> dict:
    """Декодирует JWT"""
    return jwt.decode(token, settings.jwt.secret_key, [settings.jwt.algorithm])
