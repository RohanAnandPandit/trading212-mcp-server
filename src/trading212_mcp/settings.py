"""Validated startup configuration; importing the package has no side effects."""

import os
from pathlib import Path
from typing import Literal, Self

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, hide_input_in_errors=True)

    api_key: SecretStr
    api_secret: SecretStr | None = None
    environment: Literal["demo", "live"] = "demo"
    transport: Literal["stdio", "sse", "streamable-http"] = "stdio"
    cache_dir: Path = Path(".cache/trading212-v3")
    account_ttl: float = Field(default=15, ge=0, allow_inf_nan=False)
    history_ttl: float = Field(default=300, ge=0, allow_inf_nan=False)
    metadata_ttl: float = Field(default=3600, ge=0, allow_inf_nan=False)

    @field_validator("api_key")
    @classmethod
    def key_not_empty(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("TRADING212_API_KEY must be configured")
        return value

    @classmethod
    def from_env(cls) -> Self:
        # Read only the explicitly located working-directory file, not parents.
        load_dotenv(Path.cwd() / ".env", override=False)
        return cls.model_validate(
            {
                "api_key": os.getenv("TRADING212_API_KEY", ""),
                "api_secret": os.getenv("TRADING212_API_SECRET") or None,
                "environment": os.getenv("ENVIRONMENT", "demo"),
                "transport": os.getenv("TRANSPORT", "stdio"),
                "cache_dir": os.getenv("TRADING212_CACHE_DIR", ".cache/trading212-v3"),
                "account_ttl": os.getenv("TRADING212_ACCOUNT_TTL", "15"),
                "history_ttl": os.getenv("TRADING212_HISTORY_TTL", "300"),
                "metadata_ttl": os.getenv("TRADING212_METADATA_TTL", "3600"),
            }
        )
