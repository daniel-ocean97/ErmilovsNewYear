import asyncio
import logging
from datetime import datetime

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from celery_app import celery_app

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Просто хардкодим значения - никаких конфигов!
BOT_TOKEN = "8584136497:AAFKfBxijQ1qmWRsGVls-iwLTygIKmi0g4Q"
TEST_CHAT_ID = "415348893"  # Замените на ваш ID

# Задача 1: Простой тест
@celery_app.task
def send_test_message():
    async def _send():
        bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        try:
            await bot.send_message(
                TEST_CHAT_ID,
                f"✅ Тест Celery!\nВремя: {datetime.now().strftime('%H:%M:%S')}"
            )
            logger.info("Сообщение отправлено!")
            return "SUCCESS"
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return f"ERROR: {e}"
        finally:
            await bot.session.close()
    
    # Используем текущий event loop или создаем новый
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_send())

# Задача 2: Тест пары (упрощённый)
@celery_app.task  
def test_pair():
    async def _send():
        bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        messages = [
            "🎉 Первое поздравление",
            "✨ Второе поздравление", 
            "❤️ Третье поздравление"
        ]
        
        try:
            for i, msg in enumerate(messages, 1):
                await bot.send_message(
                    TEST_CHAT_ID,
                    f"Тест {i}/3:\n{msg}"
                )
                await asyncio.sleep(0.5)
            
            return "PAIR_TEST_SUCCESS"
        except Exception as e:
            return f"ERROR: {e}"
        finally:
            await bot.session.close()
    
    # Используем текущий event loop или создаем новый
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_send())