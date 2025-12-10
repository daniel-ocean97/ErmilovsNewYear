from datetime import datetime

from aiogram import F, Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, PollAnswer, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Event, User
from database.repository import EventRepository, UserRepository
from database.database import async_session

quiz_router = Router()


class CreateEventStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_question = State()
    waiting_for_options = State()
    waiting_for_correct_option = State()
    waiting_for_date = State()


@quiz_router.message(Command("create_event"))
async def start_create_event(message: Message, state: FSMContext, session: AsyncSession):
    """
    Начало создания ивента
    """
    user_repo = UserRepository(session)

    # Проверяем есть ли партнер
    partner = await user_repo.get_partner(message.from_user.id)
    if not partner:
        await message.answer("❌ Сначала выбери партнера командой /partner")
        return

    await state.update_data(partner_id=partner.id)
    await message.answer(
        "📸 Пришли фотографию для этого воспоминания\n\n"
        "Это может быть любое фото, сделанное в этом году"
        "и о котором он должен будет угадать дату."
    )
    await state.set_state(CreateEventStates.waiting_for_photo)


@quiz_router.message(CreateEventStates.waiting_for_photo, F.photo)
async def process_event_photo(
        message: Message,
        state: FSMContext,
        bot: Bot
):
    """
    Получаем фото и сохраняем file_id
    """
    # Берем фото самого высокого качества
    photo = message.photo[-1]
    file_id = photo.file_id

    await state.update_data(photo_file_id=file_id)

    await message.answer(
        "✅ Фото сохранено!\n\n"
        "📝 Теперь задай вопрос для викторины\n"
        "Например: 'Когда мы были в этом месте?'"
    )
    await state.set_state(CreateEventStates.waiting_for_question)


@quiz_router.message(CreateEventStates.waiting_for_question)
async def process_event_question(
        message: Message,
        state: FSMContext
):
    """
    Получаем вопрос для викторины
    """
    await state.update_data(question=message.text)

    await message.answer(
        "📋 Теперь введи варианты ответов\n\n"
        "Формат: каждый вариант с новой строки\n"
        "Пример:\n"
        "17 июня\n"
        "27 июня\n"
        "13 июля\n"
    )
    await state.set_state(CreateEventStates.waiting_for_options)


@quiz_router.message(CreateEventStates.waiting_for_options)
async def process_event_options(
        message: Message,
        state: FSMContext
):
    """
    Получаем варианты ответов
    """
    options = [opt.strip() for opt in message.text.split('\n') if opt.strip()]

    if len(options) < 2:
        await message.answer("❌ Нужно минимум 2 варианта ответа")
        return

    await state.update_data(options=options)

    # Создаем клавиатуру для выбора правильного варианта
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=option, callback_data=f"correct_{i}")]
        for i, option in enumerate(options)
    ])

    await message.answer(
        "✅ Варианты сохранены!\n\n"
        "🎯 Теперь выбери ПРАВИЛЬНЫЙ вариант:",
        reply_markup=keyboard
    )
    await state.set_state(CreateEventStates.waiting_for_correct_option)


@quiz_router.callback_query(CreateEventStates.waiting_for_correct_option, F.data.startswith("correct_"))
async def create_and_send_quiz(
        callback: CallbackQuery,
        state: FSMContext,
        session: AsyncSession,
        bot: Bot
):
    """
    Создаем викторину и отправляем партнеру
    """
    # 1. Получаем ID выбранного варианта
    option_id = int(callback.data.split("_")[1])

    # 2. Получаем все данные из состояния
    data = await state.get_data()
    await state.update_data(correct_option_id=option_id)

    event_repo = EventRepository(session)
    user_repo = UserRepository(session)

    # 3. Получаем создателя
    creator = await user_repo.get_user(callback.from_user.id)
    if not creator:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        await state.clear()
        return

    # 4. Получаем партнера
    partner = await user_repo.get_user_by_id(data['partner_id'])
    if not partner:
        await callback.answer("❌ Партнер не найден", show_alert=True)
        await state.clear()
        return

    # 5. Отправляем фото партнеру если есть
    if data.get('photo_file_id'):
        await bot.send_photo(
            chat_id=partner.telegram_id,
            photo=data['photo_file_id'],
            caption="🎬 Вспомни, когда это было?"
        )

    # 6. Создаем и отправляем викторину
    try:
        poll_msg = await bot.send_poll(
            chat_id=partner.telegram_id,
            question=data['question'],
            options=data['options'],
            type="quiz",
            correct_option_id=option_id,
            is_anonymous=False,
            open_period=6000  # 100 минут на ответ
        )

        # 7. Сохраняем в БД
        await event_repo.create_event(
            creator_id=creator.id,
            partner_id=partner.id,
            question=data['question'],
            options=data['options'],
            correct_option_id=option_id,
            telegram_poll_id=poll_msg.poll.id,
            photo_file_id=data.get('photo_file_id'),
            explanation=f"Правильный ответ: {data['options'][option_id]}"
        )

        # 8. Уведомляем создателя
        await callback.message.edit_text(
            f"✅ Викторина отправлена {partner.first_name}!\n\n"
            f"❓ Вопрос: {data['question']}\n"
            f"✅ Правильный ответ: {data['options'][option_id]}\n\n"
            f"Ждем ответа партнера!"
        )

        # 9. Очищаем состояние (цикл завершен)
        await state.clear()

        # 10. Отвечаем на колбэк
        await callback.answer()

    except Exception as e:
        print(f"Ошибка создания викторины: {e}")
        await callback.answer("❌ Ошибка при создании викторины", show_alert=True)
        await state.clear()


@quiz_router.poll_answer()
async def handle_quiz_answer(poll_answer: PollAnswer, bot: Bot):
    """
    Обработчик ответов на викторину
    """
    async with async_session() as session:
        # 1. Находим событие по ID викторины
        stmt = select(Event).where(Event.telegram_poll_id == poll_answer.poll_id)
        result = await session.execute(stmt)
        event = result.scalar_one_or_none()

        if not event:
            return

        # 2. Находим пользователей
        creator_stmt = select(User).where(User.id == event.creator_id)
        creator_result = await session.execute(creator_stmt)
        creator = creator_result.scalar_one_or_none()

        if not creator:
            return

        # 3. Проверяем ответ
        user_answer = poll_answer.option_ids[0] if poll_answer.option_ids else None
        is_correct = (user_answer == event.correct_option_id)

        # 4. Отправляем сообщения
        if is_correct:
            await bot.send_message(
                chat_id=creator.telegram_id,
                text=f"🎯 {poll_answer.user.first_name} правильно угадал!\n"
                     f"Теперь ты должен создать послание командой /congratulate"
            )

            # 5. Обновляем статус
            update_stmt = update(Event).where(Event.id == event.id).values(is_completed=True)
            await session.execute(update_stmt)
            await session.commit()

            await bot.send_message(
                chat_id=poll_answer.user.id,
                text="✅ Правильно! Теперь твой партнер должен создать послание"
            )
        else:
            # Получаем правильный вариант текста
            correct_option_text = event.options[event.correct_option_id] if event.options else str(
                event.correct_option_id)
            await bot.send_message(
                chat_id=poll_answer.user.id,
                text=f"❌ Неправильно. Правильный ответ - {correct_option_text}\n"
                     f"Теперь ты должен создать послание командой /congratulate"
            )
            await bot.send_message(
                chat_id=creator.telegram_id,
                text=f"🎯 {poll_answer.user.first_name} ответил(а) не правильно!\n"
                     f"Теперь он создаст послание"
            )