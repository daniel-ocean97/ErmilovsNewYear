from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from database.repository import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession


class UserCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        session: AsyncSession = data.get("session")
        message = event.message if hasattr(event, "message") else event

        if session and hasattr(message, "from_user"):
            user_repo = UserRepository(session)
            user = await user_repo.get_user(message.from_user.id)

            if not user:
                await message.answer("❌ Сначала зарегистрируйтесь через /start")
                return

            data["db_user"] = user  # Добавляем пользователя в data

        return await handler(event, data)
