from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PT_", env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./data/terminal.db"
    poll_seconds: float = Field(default=15, ge=5)
    max_age_seconds: float = Field(default=45, ge=1)
    max_skew_seconds: float = Field(default=20, ge=0)
    requests_per_second: float = Field(default=3, gt=0, le=20)
    retention_days: int = Field(default=7, ge=1)
    kalshi_api_key_id: SecretStr = SecretStr("")
    kalshi_private_key_path: str = ""
