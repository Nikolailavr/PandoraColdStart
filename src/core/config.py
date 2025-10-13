import logging
from pathlib import Path
from typing import Literal, List

from aiogram import Bot
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

LOG_DEFAULT_FORMAT = (
    "[%(asctime)s] | %(module)20s:%(lineno)-4d | %(levelname)-8s - %(message)s"
)

SCHEDULE_FILE = BASE_DIR / "data/schedule.json"


class LoggingConfig(BaseModel):
    log_level: Literal[
        "debug",
        "info",
        "warning",
        "error",
        "critical",
    ] = "info"
    log_format: str = LOG_DEFAULT_FORMAT
    # log_path: str = "app.log"

    @property
    def log_level_value(self) -> int:
        return logging.getLevelNamesMapping()[self.log_level.upper()]


class Telegram(BaseModel):
    token: str
    admin_chat_ids: List[int]

    @field_validator("admin_chat_ids", mode="before")
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):  # JSON
                import json

                return json.loads(v)
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v


class Pandora(BaseModel):
    login: str
    password: str


class Schedule(BaseModel):
    interval: int


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            BASE_DIR / ".env.template",
            BASE_DIR / ".env",
        ),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )
    logging: LoggingConfig = LoggingConfig()
    pandora: Pandora
    telegram: Telegram


settings = Settings()

# Logging
logging.basicConfig(
    level=settings.logging.log_level_value,
    format=settings.logging.log_format,
)

bot = Bot(token=settings.telegram.token)
