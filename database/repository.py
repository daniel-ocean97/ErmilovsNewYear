from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Congratulation, Event, User
from .database import async_session


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> User | None:  # Добавлено
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        telegram_id: int,
        username: str = None,
        first_name: str = "",
        last_name: str = None,
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def set_partner(self, user_id: int, partner_telegram_id: int) -> bool:
        partner = await self.get_user(partner_telegram_id)
        if not partner:
            return False

        user = await self.get_user(user_id)
        if user:
            user.partner_id = partner.id
            await self.session.commit()
            return True
        return False

    async def get_partner(self, telegram_id: int) -> User | None:
        user = await self.get_user(telegram_id)
        if user and user.partner_id:
            return await self.get_user_by_id(user.partner_id)
        return None


class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_event(
        self,
        creator_id: int,
        partner_id: int,
        question: str,
        options: list[str],
        correct_option_id: int,
        telegram_poll_id: str = None,
        photo_file_id: str = None,
        explanation: str = None,
    ) -> Event:
        """
        Создать ивент БЕЗ даты
        """
        event = Event(
            creator_id=creator_id,
            partner_id=partner_id,
            question=question,
            options=options,
            correct_option_id=correct_option_id,
            telegram_poll_id=telegram_poll_id,
            photo_file_id=photo_file_id,
            explanation=explanation,
        )
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def get_event_by_poll_id(self, poll_id: str) -> Event | None:
        stmt = select(Event).where(Event.telegram_poll_id == poll_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_event_completed(self, event_id: int) -> None:  # Один метод
        stmt = update(Event).where(Event.id == event_id).values(is_completed=True)
        await self.session.execute(stmt)
        await self.session.commit()


class CongratulationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_congratulation(
        self, sender_id: int, message: str, photo_file_id: str = None
    ) -> Congratulation:
        """Создать поздравление"""
        congratulation = Congratulation(
            sender_id=sender_id, message=message, photo_file_id=photo_file_id
        )
        self.session.add(congratulation)
        await self.session.commit()
        await self.session.refresh(congratulation)
        return congratulation

    async def list_by_sender(self, sender_id: int) -> list[Congratulation]:
        """Получить все поздравления пользователя, новые первыми"""
        stmt = (
            select(Congratulation)
            .where(Congratulation.sender_id == sender_id)
            .order_by(Congratulation.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


# ===== Utils for broadcast =====
async def get_all_chat_ids() -> list[int]:
    """Вернуть все telegram_id пользователей для рассылки."""
    async with async_session() as session:
        result = await session.execute(select(User.telegram_id))
        # scalars() возвращает генератор, превращаем в список
        return list(result.scalars().all())


async def remove_chat_id(chat_id: int) -> None:
    """
    Удалить пользователя из рассылки.
    Если есть внешние связи, просто пропускаем ошибку, чтобы не падать при рассылке.
    """
    async with async_session() as session:
        try:
            await session.execute(delete(User).where(User.telegram_id == chat_id))
            await session.commit()
        except Exception:
            # Не ломаем поток уведомлений, логирование можно добавить позже
            await session.rollback()


async def get_all_partner_pairs() -> list[dict]:
    """
    Получить все пары партнеров с их поздравлениями.
    Возвращает список словарей с информацией о паре и поздравлениях.
    Учитывает только взаимные пары (когда оба пользователя выбрали друг друга).
    """
    async with async_session() as session:
        # Получаем всех пользователей с партнерами
        stmt = select(User).where(User.partner_id.isnot(None))
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        pairs = []
        processed_pairs = set()  # Чтобы не дублировать пары
        
        for user in users:
            if user.id in processed_pairs:
                continue
                
            partner = await session.get(User, user.partner_id)
            if not partner:
                continue
            
            # Проверяем, что партнер тоже выбрал этого пользователя (взаимная пара)
            if partner.partner_id != user.id:
                continue
            
            # Получаем поздравления от пользователя к партнеру
            user_congrats_stmt = select(Congratulation).where(
                Congratulation.sender_id == user.id
            )
            user_congrats_result = await session.execute(user_congrats_stmt)
            user_congrats = list(user_congrats_result.scalars().all())
            
            # Получаем поздравления от партнера к пользователю
            partner_congrats_stmt = select(Congratulation).where(
                Congratulation.sender_id == partner.id
            )
            partner_congrats_result = await session.execute(partner_congrats_stmt)
            partner_congrats = list(partner_congrats_result.scalars().all())
            
            pairs.append({
                "user1": {
                    "telegram_id": user.telegram_id,
                    "first_name": user.first_name,
                    "congratulations": [
                        {
                            "message": c.message,
                            "photo_file_id": c.photo_file_id
                        }
                        for c in user_congrats
                    ]
                },
                "user2": {
                    "telegram_id": partner.telegram_id,
                    "first_name": partner.first_name,
                    "congratulations": [
                        {
                            "message": c.message,
                            "photo_file_id": c.photo_file_id
                        }
                        for c in partner_congrats
                    ]
                }
            })
            
            # Помечаем обе стороны пары как обработанные
            processed_pairs.add(user.id)
            processed_pairs.add(partner.id)
        
        return pairs