from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from .models import User, Event, Congratulation
from datetime import datetime

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

    async def create_user(self, telegram_id: int, username: str = None,
                          first_name: str = "", last_name: str = None) -> User:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
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
            correct_date: datetime,
            telegram_poll_id: str = None,
            photo_file_id: str = None,
            explanation: str = None
    ) -> Event:
        event = Event(
            creator_id=creator_id,
            partner_id=partner_id,
            question=question,
            options=options,
            correct_option_id=correct_option_id,
            correct_date=correct_date,
            telegram_poll_id=telegram_poll_id,
            photo_file_id=photo_file_id,
            explanation=explanation
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