from sqlalchemy import BigInteger, String, Text, DateTime, Boolean, ForeignKey, ARRAY, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List


class Base(DeclarativeBase):
    pass


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(100))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    partner_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Связи
    partner: Mapped[Optional["User"]] = relationship(
        "User",
        remote_side=[id],
        backref="partners",
        foreign_keys=[partner_id],
        uselist=False
    )

    # События, созданные пользователем
    created_events: Mapped[List["Event"]] = relationship(
        "Event",
        back_populates="creator",
        foreign_keys="Event.creator_id"
    )

    # События, где пользователь является партнером
    partner_events: Mapped[List["Event"]] = relationship(
        "Event",
        back_populates="partner_user",
        foreign_keys="Event.partner_id"
    )


class Event(Base):
    """Модель ивента (воспоминания с фотографией)"""
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    creator_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    partner_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)

    photo_file_id: Mapped[Optional[str]] = mapped_column(String(500))
    question: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list[str]] = mapped_column(ARRAY(String(100)), nullable=False)
    correct_option_id: Mapped[int] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    explanation: Mapped[Optional[str]] = mapped_column(Text)
    telegram_poll_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True)

    creator: Mapped["User"] = relationship("User", foreign_keys=[creator_id], back_populates="created_events")
    partner_user: Mapped["User"] = relationship("User", foreign_keys=[partner_id], back_populates="partner_events")



class Congratulation(Base):
    __tablename__ = "congratulations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sender_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    photo_file_id: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Только связь с пользователем
    sender: Mapped["User"] = relationship("User")