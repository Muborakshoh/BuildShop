from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


_INSECURE_KEYS = frozenset({
    "dev-secret-change-me",
    "change-this-secret-in-production",
})


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
    site_url: str = "http://localhost:8000"
    public_setting_groups: list[str] = Field(default_factory=lambda: ["general", "contacts", "identity", "social"])

    # Telegram Bot
    telegram_bot_token: str | None = None
    telegram_bot_username: str | None = None  # without @
    telegram_admin_chat_id: str | None = None  # channel/group id for admin alerts

    # Delivery zones
    delivery_free_threshold: float = 500.0  # free delivery above this order total (somoni)
    delivery_default_price: float = 30.0  # default delivery price (somoni)

    # Explicit flag: allow registration without email verification
    allow_registration_without_email: bool = False

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    def validate_secret_key(self) -> None:
        if self.secret_key in _INSECURE_KEYS:
            raise RuntimeError(
                "SECRET_KEY использует небезопасное значение по умолчанию! "
                "Укажите надёжный SECRET_KEY в .env перед запуском."
            )


settings = Settings()
