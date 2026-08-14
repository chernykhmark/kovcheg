# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    BOT_TOKEN: str
    DATABASE_URL: str
    ADMIN_CHAT_ID: int
    SBP_CARD: str
    SBP_PHONE: str
    SBP_NAME: str
    SBP_BANK: str
    TICKET_PRICE: int
    # HTTPS-адрес опубликованного лендинга. Если не задан, кнопка Mini App скрыта.
    WEB_APP_URL: str | None = None


settings = Settings()
