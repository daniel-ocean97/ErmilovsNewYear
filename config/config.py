from dataclasses import dataclass
from environs import Env


@dataclass
class TgBot:
    token: str  # Токен для доступа к телеграм-боту


@dataclass
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    database: str


@dataclass
class LogSettings:
    level: str
    format: str


@dataclass
class Config:
    bot: TgBot
    db: DatabaseConfig
    log: LogSettings


def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(
        bot=TgBot(token=env("BOT_TOKEN")),
        db=DatabaseConfig(
            host=env("DB_HOST", "localhost"),
            port=env.int("DB_PORT", 5432),
            user=env("DB_USER", "postgres"),
            password=env("DB_PASSWORD", ""),
            database=env("DB_NAME", "year_summary_bot"),
        ),
        log=LogSettings(level=env("LOG_LEVEL"), format=env("LOG_FORMAT")),
    )