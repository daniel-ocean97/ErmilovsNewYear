import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config.config import Config, load_config
from database.database import init_db
from handlers.other import other_router
from handlers.user import user_router
from handlers.quiz_handlers import quiz_router
from middleware.database import DatabaseMiddleware

logger = logging.getLogger(__name__)


async def main():
    config: Config = load_config()

    logging.basicConfig(
        level=logging.getLevelName(level=config.log.level),
        format=config.log.format,
    )

    logger.info("Starting bot")

    # Инициализируем базу данных
    await init_db()

    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Регистрируем middleware для всех роутеров
    routers = [user_router, other_router, quiz_router]
    for router in routers:
        router.message.middleware(DatabaseMiddleware())
        router.callback_query.middleware(DatabaseMiddleware())

    # Регистрируем роутеры
    dp.include_router(user_router)
    dp.include_router(quiz_router)
    dp.include_router(other_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())