from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import async_session


class DatabaseMiddleware(BaseMiddleware):
    """
    Middleware для внедрения сессии БД в хэндлеры
    """

    async def __call__(
            self,
            handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
            event: Any,  # Любой тип события
            data: Dict[str, Any]
    ) -> Any:
        # Создаем новую сессию для каждого запроса
        async with async_session() as session:
            # Добавляем сессию в data (будет доступна в хэндлере)
            data['session'] = session

            try:
                # Вызываем хэндлер
                result = await handler(event, data)
                # Коммитим изменения
                await session.commit()
                return result
            except Exception as e:
                # Откатываем в случае ошибки
                await session.rollback()
                raise
            finally:
                # Закрываем сессию
                await session.close()