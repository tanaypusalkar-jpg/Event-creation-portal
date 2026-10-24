from pathlib import Path
from sqlalchemy.engine import make_url

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = Field(
        description="SQLAlchemy URL, for example mysql+pymysql://user:password@127.0.0.1:3306/event_portal"
    )
    test_database_url: str | None = None
    jwt_secret: str = Field(min_length=32)
    jwt_expire_minutes: int = Field(default=20, ge=1, le=1440)
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    frontend_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    admin_email: str = "admin@example.com"
    admin_password: str = "change-me"

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        try:
            parsed = make_url(value)
        except Exception as exc:
            raise ValueError(
                "DATABASE_URL is invalid. Use mysql+pymysql://USER:PASSWORD@HOST:3306/DATABASE."
            ) from exc
        if parsed.drivername != "mysql+pymysql":
            raise ValueError(
                "This project is configured for MySQL. DATABASE_URL must start with "
                "'mysql+pymysql://'."
            )
        if not parsed.database:
            raise ValueError("DATABASE_URL must include the MySQL database name.")
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.frontend_origins.split(",") if origin.strip()]


settings = Settings()
