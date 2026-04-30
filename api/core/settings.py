from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, cast


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="api/.env", extra="ignore")

    ENV: str = "dev"

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    TRUSTED_PROXY_IPS: list[str] = ["127.0.0.1", "::1"]
    CORS_ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    COOKIE_NAME: str = "refresh_token"
    COOKIE_HTTPONLY: bool = True
    COOKIE_SECURE: bool | None = None
    COOKIE_SAMESITE: str | None = None
    COOKIE_MAX_AGE_SECONDS: int = 60 * 60 * 24 * 31
    COOKIE_DOMAIN: str | None = None
    COOKIE_PATH: str = "/"

    @field_validator("TRUSTED_PROXY_IPS", "CORS_ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_csv_list(cls, value: list[str] | str) -> list[str]:
        if isinstance(value, list):
            return value
        return [item.strip() for item in value.split(",") if item.strip()]

    @field_validator("ENV")
    @classmethod
    def validate_env(cls, value: str) -> str:
        allowed = {"dev", "staging", "prod"}
        normalized = value.strip().lower()
        if normalized not in allowed:
            raise ValueError(f"ENV must be one of {allowed}")
        return normalized

    @field_validator("COOKIE_SAMESITE")
    @classmethod
    def validate_cookie_samesite(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip().lower()
        allowed = {"lax", "strict", "none"}
        if normalized not in allowed:
            raise ValueError("COOKIE_SAMESITE must be one of: lax, strict, none")
        return normalized

    @model_validator(mode="after")
    def validate_cookie_compat(self) -> "Settings":
        if self.samesite_cookie == "none" and not self.secure_cookie:
            raise ValueError("SameSite=None requires secure cookies (COOKIE_SECURE=true)")
        return self

    @property
    def secure_cookie(self) -> bool:
        if self.COOKIE_SECURE is not None:
            return self.COOKIE_SECURE
        return self.ENV in {"staging", "prod"}

    @property
    def samesite_cookie(self) -> Literal["lax", "strict", "none"]:
        if self.COOKIE_SAMESITE is not None:
            return cast(Literal["lax", "strict", "none"], self.COOKIE_SAMESITE)
        return "lax" if self.ENV == "dev" else "strict"


settings = Settings()  # pyright: ignore[reportCallIssue]
