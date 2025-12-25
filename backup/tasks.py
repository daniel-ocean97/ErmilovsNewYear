import asyncio
import logging
import random
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from celery import Task
from celery.schedules import crontab

from celery_app import celery_app
from config.config import load_config
from database.repository import get_all_partner_pairs

logger = logging.getLogger(__name__)

# Конфигурация будет загружаться внутри функций, а не при импорте
_config = None

def get_config():
    """Ленивая загрузка конфигурации"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


class AsyncTask(Task):
    """Класс для выполнения асинхронных задач в Celery"""
    _bot = None

    @property
    def bot(self):
        if self._bot is None:
            cfg = get_config()
            self._bot = Bot(
                token=cfg.bot.token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            )
        return self._bot


@celery_app.task(base=AsyncTask, bind=True)
def send_congratulations_to_pair(self, pair_data: dict):
    """Отправка поздравлений паре партнеров - каждое поздравление приходит обоим партнерам"""
    async def _send():
        bot = self.bot
        user1 = pair_data["user1"]
        user2 = pair_data["user2"]
        
        # Отправляем поздравления от user1 обоим партнерам
        for congrat in user1["congratulations"]:
            try:
                # Отправляем user1
                if congrat["photo_file_id"]:
                    await bot.send_photo(
                        chat_id=user1["telegram_id"],
                        photo=congrat["photo_file_id"],
                        caption=congrat["message"]
                    )
                else:
                    await bot.send_message(
                        chat_id=user1["telegram_id"],
                        text=congrat["message"]
                    )
                await asyncio.sleep(0.04)  # ~25 msg/сек
                
                # Отправляем user2
                if congrat["photo_file_id"]:
                    await bot.send_photo(
                        chat_id=user2["telegram_id"],
                        photo=congrat["photo_file_id"],
                        caption=congrat["message"]
                    )
                else:
                    await bot.send_message(
                        chat_id=user2["telegram_id"],
                        text=congrat["message"]
                    )
                await asyncio.sleep(0.04)  # ~25 msg/сек
            except Exception as e:
                logger.error(f"Ошибка отправки поздравления от {user1['telegram_id']}: {e}")
        
        # Отправляем поздравления от user2 обоим партнерам
        for congrat in user2["congratulations"]:
            try:
                # Отправляем user1
                if congrat["photo_file_id"]:
                    await bot.send_photo(
                        chat_id=user1["telegram_id"],
                        photo=congrat["photo_file_id"],
                        caption=congrat["message"]
                    )
                else:
                    await bot.send_message(
                        chat_id=user1["telegram_id"],
                        text=congrat["message"]
                    )
                await asyncio.sleep(0.04)  # ~25 msg/сек
                
                # Отправляем user2
                if congrat["photo_file_id"]:
                    await bot.send_photo(
                        chat_id=user2["telegram_id"],
                        photo=congrat["photo_file_id"],
                        caption=congrat["message"]
                    )
                else:
                    await bot.send_message(
                        chat_id=user2["telegram_id"],
                        text=congrat["message"]
                    )
                await asyncio.sleep(0.04)  # ~25 msg/сек
            except Exception as e:
                logger.error(f"Ошибка отправки поздравления от {user2['telegram_id']}: {e}")
    
    asyncio.run(_send())


@celery_app.task
def schedule_all_congratulations():
    """Планирование отправки всех поздравлений"""
    # Проверяем, что мы в 2026 году
    current_year = datetime.now().year
    if current_year != 2026:
        logger.info(f"Пропускаем планирование, текущий год: {current_year}, ожидается 2026")
        return
    
    async def _schedule():
        pairs = await get_all_partner_pairs()
        
        if not pairs:
            logger.info("Нет пар партнеров для отправки поздравлений")
            return
        
        # Первое сообщение в 00:00 01.01.2026
        first_send_time = datetime(2026, 1, 1, 0, 0, 0)
        
        # Конечная дата - 13.01.2026 23:59:59
        end_date = datetime(2026, 1, 13, 23, 59, 59)
        
        # Генерируем случайные времена для каждой пары
        for pair in pairs:
            # Первое сообщение в 00:00
            send_congratulations_to_pair.apply_async(
                args=[pair],
                eta=first_send_time
            )
            
            # Генерируем 2-3 дополнительных сообщения в случайное время до 13.01.2026
            num_additional = random.randint(2, 3)
            for _ in range(num_additional):
                # Случайное время между 01.01.2026 00:01 и 13.01.2026 23:59
                random_seconds = random.randint(60, int((end_date - first_send_time).total_seconds()))
                random_time = first_send_time + timedelta(seconds=random_seconds)
                
                send_congratulations_to_pair.apply_async(
                    args=[pair],
                    eta=random_time
                )
        
        logger.info(f"Запланирована отправка поздравлений для {len(pairs)} пар")
    
    asyncio.run(_schedule())


# Настройка расписания Celery Beat - запускаем планировщик в 00:00 01.01.2026
# Задача сама запланирует все остальные сообщения
celery_app.conf.beat_schedule = {
    "schedule-congratulations": {
        "task": "tasks.schedule_all_congratulations",
        "schedule": crontab(hour=0, minute=0, day_of_month=1, month_of_year=1),
        "args": (),
    },
}

