# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_admin_ids(value: str) -> frozenset[int]:
    """Parse comma-separated Telegram administrator IDs."""
    if not value.strip():
        return frozenset()

    try:
        return frozenset(
            int(item.strip()) for item in value.split(",") if item.strip()
        )
    except ValueError as exc:
        raise ValueError("ADMIN_IDS must contain comma-separated Telegram user IDs") from exc


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    BOT_TOKEN: str
    DATABASE_URL: str
    # Legacy single-administrator setting. ADMIN_IDS takes precedence.
    ADMIN_CHAT_ID: int | None = None
    ADMIN_IDS: str = ""
    SBP_CARD: str
    SBP_PHONE: str
    SBP_NAME: str
    SBP_BANK: str
    TICKET_PRICE: int
    # Необязательный SOCKS/HTTP-прокси для подключения к Telegram API.
    PROXY_URL: str | None = None
    # HTTPS-адрес опубликованного лендинга. Если не задан, кнопка Mini App скрыта.
    WEB_APP_URL: str | None = None

    @property
    def admin_ids(self) -> frozenset[int]:
        ids = parse_admin_ids(self.ADMIN_IDS)
        if ids:
            return ids
        if self.ADMIN_CHAT_ID is not None and self.ADMIN_CHAT_ID > 0:
            return frozenset({self.ADMIN_CHAT_ID})
        return frozenset()


settings = Settings()
