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
class RedisConfig:
    host: str
    port: int
    db: int


@dataclass
class LogSettings:
    level: str
    format: str


@dataclass
class Config:
    bot: TgBot
    db: DatabaseConfig
    redis: RedisConfig
    log: LogSettings


def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(
        bot=TgBot(token=env("BOT_TOKEN")),
        db=DatabaseConfig(
            host=env("DB_HOST"),
            port=env.int("DB_PORT"),
            user=env("DB_USER", "postgres"),
            password=env("DB_PASSWORD", ""),
            database=env("DB_NAME", "year_summary_bot"),
        ),
        redis=RedisConfig(
            host=env("REDIS_HOST", "localhost"),
            port=env.int("REDIS_PORT", 6379),
            db=env.int("REDIS_DB", 0),
        ),
        log=LogSettings(level=env("LOG_LEVEL"), format=env("LOG_FORMAT")),
    )
