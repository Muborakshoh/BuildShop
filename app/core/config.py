from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://buildshop:buildshop_password@localhost:5432/buildshop"
    secret_key: str = "dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:8000", "http://127.0.0.1:8000"])
    first_admin_email: str | None = None
    first_admin_password: str | None = None
    first_admin_name: str = "BuildShop Admin"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str = "noreply@buildshop.local"
    smtp_use_tls: bool = True
    admin_notification_email: str | None = None
    registration_code_expire_minutes: int = 15

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
