import os
from celery import Celery
from environs import Env

# Загружаем только Redis настройки, без полной конфигурации
env = Env()
env.read_env()

redis_host = env("REDIS_HOST", "localhost")
redis_port = env.int("REDIS_PORT", 6379)
redis_db = env.int("REDIS_DB", 0)

celery_app = Celery(
    "newyear_bot",
    broker=f"redis://{redis_host}:{redis_port}/{redis_db}",
    backend=f"redis://{redis_host}:{redis_port}/{redis_db}",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
)

# Импортируем все модули с задачами, чтобы worker их видел
# Это нужно для автоматической регистрации задач
# Используем широкий except, чтобы не ломать worker при ошибках импорта
try:
    import tasks  # Основные задачи
except Exception as e:
    import logging
    logging.warning(f"Не удалось импортировать tasks: {e}")

try:
    import celery_test  # Тестовые задачи
except Exception as e:
    import logging
    logging.warning(f"Не удалось импортировать celery_test: {e}")

