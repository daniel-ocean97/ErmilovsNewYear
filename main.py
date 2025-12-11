import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import (
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeAllPrivateChats,
)
from config.config import Config, load_config
from database.database import init_db
from handlers.congratulation_handlers import congratulation_router
from handlers.other import other_router
from handlers.user import user_router
from handlers.quiz_handlers import quiz_router
from middleware.database import DatabaseMiddleware
from database.repository import get_all_chat_ids, remove_chat_id

logger = logging.getLogger(__name__)


async def notify_all(bot: Bot, text: str):
    "Оповещение всех пользователей об обновлении"
    for chat_id in await get_all_chat_ids():
        try:
            await bot.send_message(chat_id, text)
            await asyncio.sleep(0.04)  # ~25 msg/сек
        except Exception as e:
            if "Forbidden" in str(e) or "403" in str(e):
                await remove_chat_id(chat_id)


async def set_bot_commands(bot: Bot):
    """Устанавливаем команды бота в меню слева от поля ввода"""
    commands = [
        BotCommand(command="start", description="🎉 Начать работу с ботом"),
        BotCommand(command="help", description="📖 Правила игры"),
        BotCommand(command="create_event", description="🎮 Создать воспоминание"),
        BotCommand(command="partner", description="👫 Выбрать партнёра"),
        BotCommand(command="congratulate", description="💌 Написать послание"),
        BotCommand(command="my_congratulations", description="📦 Мои послания"),
    ]
    logger.info(f"Setting commands: {commands}")
    try:
        result = await bot.set_my_commands(
            commands=commands, scope=BotCommandScopeAllPrivateChats()
        )
        logger.info(f"Commands set successfully: {result}")
        return True
    except Exception as e:
        logger.error(f"Error setting commands: {e}")
        return False


async def main():
    config: Config = load_config()

    logging.basicConfig(
        level=logging.getLevelName(level=config.log.level),
        format=config.log.format,
    )

    logger.info("Starting bot")

    # Инициализация базы данных
    await init_db()

    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Регистрируем middleware для всех роутеров
    routers = [user_router, other_router, quiz_router, congratulation_router]
    for router in routers:
        router.message.middleware(DatabaseMiddleware())
        router.callback_query.middleware(DatabaseMiddleware())

    # Регистрируем роутеры
    dp.include_router(user_router)  # 1. Основные команды (/start, /help, /partner)
    dp.include_router(quiz_router)  # 2. Викторины
    dp.include_router(congratulation_router)  # 3. Поздравления
    dp.include_router(other_router)  # 4. "Эхо в ответ"

    # Устанавливаем команды бота
    try:
        await set_bot_commands(bot)
        logger.info("Bot commands set successfully")
    except Exception as e:
        logger.warning(f"Could not set bot commands: {e}")

    await bot.delete_webhook(drop_pending_updates=True)
    # Оповещение всех пользователей об обновлении
    # await notify_all(
    #     bot,
    #     "🎉 Вышло обновление!\nТеперь при неправильном ответе партнера, создателю приходит какой вариант был выбран",
    # )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
