from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    name: str = "WorkTime Sync"
    debug: bool = True


class DatabaseSettings(BaseSettings):
    url: str
    pool_size: int = 10
    max_overflow: int = 20


class JWTSettings(BaseSettings):
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


class Settings(BaseSettings):
    app: AppSettings
    database: DatabaseSettings
    jwt: JWTSettings

    model_config = ConfigDict(env_file=".env", env_nested_delimiter="__")


settings = Settings()
