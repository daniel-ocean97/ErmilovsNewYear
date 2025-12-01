from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from models import User, Event, EventAnswer, Congratulation
from datetime import datetime


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, telegram_id: int) -> User | None:
        """Получить пользователя по Telegram ID"""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, telegram_id: int, username: str = None,
                          first_name: str = "", last_name: str = None) -> User:
        """Создать нового пользователя"""
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            partner_id=None
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def set_partner(self, user_id: int, partner_telegram_id: int) -> bool:
        """Установить партнера для пользователя"""
        # Находим партнера
        stmt = select(User).where(User.telegram_id == partner_telegram_id)
        result = await self.session.execute(stmt)
        partner = result.scalar_one_or_none()

        if not partner:
            return False

        # Обновляем пользователя
        stmt = update(User).where(User.telegram_id == user_id).values(partner_id=partner.id)
        await self.session.execute(stmt)
        await self.session.commit()
        return True

    async def get_partner(self, telegram_id: int) -> User | None:
        """Получить партнера пользователя"""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if user and user.partner_id:
            stmt = select(User).where(User.id == user.partner_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()

        return None


class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_event(self, creator_id: int, partner_id: int,
                           photo_file_id: str, question: str,
                           correct_date: datetime, answers: list[datetime]) -> Event:
        """Создать новый ивент с вариантами ответов"""
        event = Event(
            creator_id=creator_id,
            partner_id=partner_id,
            photo_file_id=photo_file_id,
            question=question,
            correct_date=correct_date,
            is_completed=False
        )
        self.session.add(event)
        await self.session.flush()  # Получаем ID события

        # Добавляем варианты ответов
        for answer_date in answers:
            answer = EventAnswer(
                event_id=event.id,
                answer_date=answer_date,
                is_correct=(answer_date == correct_date)
            )
            self.session.add(answer)

        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def get_user_events(self, telegram_id: int, is_completed: bool = None) -> list[Event]:
        """Получить ивенты пользователя (как созданные, так и полученные)"""
        # Находим пользователя
        user_stmt = select(User).where(User.telegram_id == telegram_id)
        user_result = await self.session.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if not user:
            return []

        # Строим запрос для событий
        stmt = select(Event).options(
            selectinload(Event.creator),
            selectinload(Event.partner_user),
            selectinload(Event.answers)
        ).where(
            (Event.creator_id == user.id) | (Event.partner_id == user.id)
        )

        if is_completed is not None:
            stmt = stmt.where(Event.is_completed == is_completed)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_event_completed(self, event_id: int) -> None:
        """Пометить ивент как завершенный"""
        stmt = update(Event).where(Event.id == event_id).values(is_completed=True)
        await self.session.execute(stmt)
        await self.session.commit()


class CongratulationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_congratulation(self, event_id: int, sender_id: int,
                                    message: str, photo_file_id: str = None) -> Congratulation:
        """Создать поздравление"""
        congratulation = Congratulation(
            event_id=event_id,
            sender_id=sender_id,
            message=message,
            photo_file_id=photo_file_id
        )
        self.session.add(congratulation)
        await self.session.commit()
        await self.session.refresh(congratulation)
        return congratulation