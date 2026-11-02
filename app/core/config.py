from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    bot_token: SecretStr

    api_base: str
    api_key: SecretStr | None = Field(default=None)
    model: str
    mcp_servers: dict[str, dict[str, Any]] = Field(default_factory=dict)

    proxy: SecretStr | None = Field(default=None)
    tg_proxy: SecretStr | None = Field(default=None)

    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = Field(default="INFO")

    check_history: bool = Field(default=False)

    @field_validator("proxy", "tg_proxy", mode="before")
    @classmethod
    def empty_value_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
