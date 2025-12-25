#!/usr/bin/env python
"""Скрипт для запуска Celery worker"""
import os
import sys

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery_app import celery_app

if __name__ == "__main__":
    # На Windows используем solo pool для работы с asyncio
    # Это решает проблему с multiprocessing и ValueError
    celery_app.worker_main([
        'worker',
        '-l', 'info',
        '--pool=solo',  # КРИТИЧНО для Windows!
    ])

