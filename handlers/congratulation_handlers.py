from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.repository import CongratulationRepository
from middleware.congratulations import UserCheckMiddleware
from database.models import User
from sqlalchemy import select
congratulation_router = Router()
congratulation_router.message.middleware(UserCheckMiddleware())


class CongratulationStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_photo = State()


@congratulation_router.message(Command("congratulate"))
async def start_congratulation(message: types.Message, state: FSMContext):
    """
    Начало создания поздравления
    """
    await message.answer(
        "🎉 Напиши текст поздравления:\n\n"
        "Это может быть любое пожелание, благодарность или теплые слова."
    )
    await state.set_state(CongratulationStates.waiting_for_message)


@congratulation_router.message(CongratulationStates.waiting_for_message)
async def process_congratulation_message(
        message: types.Message,
        state: FSMContext,
        session: AsyncSession
):
    """
    Сохраняем текст поздравления и спрашиваем про фото
    """
    congrat_text = message.text

    # Сохраняем текст в состоянии
    await state.update_data(message=congrat_text)

    await message.answer(
        f"✅ Текст сохранен!\n\n"
        f"Теперь пришли фотографию для поздравления (если хочешь)\n"
        f"Или нажмите /skip чтобы пропустить"
    )
    await state.set_state(CongratulationStates.waiting_for_photo)


@congratulation_router.message(CongratulationStates.waiting_for_photo, Command("skip"))
async def skip_congratulation_photo(
        message: types.Message,
        state: FSMContext,
        session: AsyncSession
):
    """Самый простой вариант без middleware"""
    # 1. Получаем текст
    data = await state.get_data()
    congrat_text = data.get('message', '')

    if not congrat_text:
        await message.answer("❌ Текст не найден")
        await state.clear()
        return

    # 2. Находим пользователя ПРОСТЫМ ЗАПРОСОМ

    stmt = select(User).where(User.telegram_id == message.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        await message.answer("❌ Сначала /start")
        await state.clear()
        return

    # 3. Сохраняем
    from database.models import Congratulation
    congrat = Congratulation(
        sender_id=user.id,
        message=congrat_text,
        photo_file_id=None
    )
    session.add(congrat)
    await session.commit()

    await message.answer(f"✅ Сохранено: {congrat_text}")
    await state.clear()


@congratulation_router.message(CongratulationStates.waiting_for_photo, F.photo)
async def process_congratulation_photo(
        message: types.Message,
        state: FSMContext,
        session: AsyncSession,
):
    """
    Сохраняем фото и поздравление
    """
    # Получаем данные из состояния
    data = await state.get_data()
    congrat_text = data.get('message', '')

    # 2. Находим пользователя ПРОСТЫМ ЗАПРОСОМ

    stmt = select(User).where(User.telegram_id == message.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not congrat_text:
        await message.answer("❌ Ошибка: текст поздравления не найден")
        await state.clear()
        return

    # Получаем file_id фото
    photo = message.photo[-1]
    photo_file_id = photo.file_id

    # Сохраняем в БД
    congrat_repo = CongratulationRepository(session)
    congrat = await congrat_repo.create_congratulation(
        sender_id=user.id,
        message=congrat_text,
        photo_file_id=photo_file_id
    )

    await message.answer(
        "🎊 Поздравление с фото сохранено!\n\n"
        f"Ваш текст: {congrat_text}"
    )

    await state.clear()