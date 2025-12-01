from datetime import datetime

from aiogram import F, Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, PollAnswer, PhotoSize, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository import EventRepository, UserRepository
from services.quiz_service import QuizService
from keyboards.quiz_keyboards import get_event_keyboard

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
        await message.answer("❌ Сначала выберите партнера командой /partner")
        return

    await state.update_data(partner_id=partner.id)
    await message.answer(
        "📸 Пришлите фотографию для этого воспоминания\n\n"
        "Это может быть любое фото, которое связано с вашим партнером "
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
        "📝 Теперь задайте вопрос для викторины\n"
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
        "📋 Теперь введите варианты ответов\n\n"
        "Формат: каждый вариант с новой строки\n"
        "Пример:\n"
        "Вчера\n"
        "Месяц назад\n"
        "Год назад\n"
        "Два года назад"
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
        "🎯 Теперь выберите ПРАВИЛЬНЫЙ вариант:",
        reply_markup=keyboard
    )
    await state.set_state(CreateEventStates.waiting_for_correct_option)


@quiz_router.message(CreateEventStates.waiting_for_date)
async def process_event_date(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    try:
        correct_date = datetime.strptime(message.text, "%d.%m.%Y")
        data = await state.get_data()

        # Упрощенное создание события
        event_repo = EventRepository(session)
        user_repo = UserRepository(session)
        partner = await user_repo.get_user_by_id(data['partner_id'])

        # Отправляем фото партнеру если есть
        if data.get('photo_file_id'):
            await bot.send_photo(
                chat_id=partner.telegram_id,
                photo=data['photo_file_id'],
                caption="🎬 Вспомни, когда это было?"
            )

        # Создаем викторину
        poll_msg = await bot.send_poll(
            chat_id=partner.telegram_id,
            question=data['question'],
            options=data['options'],
            type="quiz",
            correct_option_id=data['correct_option_id'],
            explanation=f"Правильная дата: {correct_date.strftime('%d.%m.%Y')}",
            is_anonymous=False
        )

        # Сохраняем в БД
        event = await event_repo.create_event(
            creator_id=message.from_user.id,
            partner_id=partner.id,
            question=data['question'],
            options=data['options'],
            correct_option_id=data['correct_option_id'],
            correct_date=correct_date,
            telegram_poll_id=poll_msg.poll.id,
            photo_file_id=data.get('photo_file_id'),
            explanation=f"Правильная дата: {correct_date.strftime('%d.%m.%Y')}"
        )

        await message.answer(f"✅ Викторина отправлена {partner.first_name}!")
        await state.clear()

    except ValueError:
        await message.answer("❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ")


@quiz_router.poll_answer()
async def handle_quiz_answer(
        poll_answer: PollAnswer,
        session: AsyncSession,
        bot: Bot
):
    """
    Обработчик ответов на викторину
    """
    # 1. Получаем репозитории
    event_repo = EventRepository(session)

    # 2. Ищем ивент по ID викторины
    event = await event_repo.get_event_by_poll_id(poll_answer.poll_id)

    if not event:
        print(f"Ивент не найден для poll_id: {poll_answer.poll_id}")
        return

    # 3. Проверяем правильность ответа
    # poll_answer.option_ids содержит список выбранных вариантов (обычно один)
    user_answer = poll_answer.option_ids[0] if poll_answer.option_ids else None

    is_correct = (user_answer == event.correct_option_id)

    # 4. Логируем ответ
    print(f"User {poll_answer.user.id} answered: {user_answer}, "
          f"correct: {event.correct_option_id}, is_correct: {is_correct}")

    # 5. Обрабатываем результат
    if is_correct:
        # Отправляем уведомление создателю
        await bot.send_message(
            chat_id=event.creator.telegram_id,
            text=f"🎯 {poll_answer.user.first_name} правильно угадал дату!\n\n"
                 f"Вопрос: {event.question}\n"
                 f"Правильная дата: {event.correct_date.strftime('%d.%m.%Y')}\n\n"
                 f"Теперь партнер должен написать поздравление."
        )

        # Отправляем уведомление отвечавшему
        await bot.send_message(
            chat_id=poll_answer.user.id,
            text=f"✅ Правильно! Вы угадали!\n\n"
                 f"Вопрос: {event.question}\n"
                 f"Правильная дата: {event.correct_date.strftime('%d.%m.%Y')}\n\n"
                 f"Теперь напишите поздравление для {event.creator.first_name} "
                 f"командой /congratulate {event.id}"
        )

        # Обновляем статус ивента
        await event_repo.mark_event_completed(event.id)

    else:
        # Отправляем уведомление о неправильном ответе
        explanation = event.explanation or f"Правильная дата: {event.correct_date.strftime('%d.%m.%Y')}"

        await bot.send_message(
            chat_id=poll_answer.user.id,
            text=f"❌ К сожалению, это не тот ответ.\n\n"
                 f"{explanation}"
        )


@quiz_router.callback_query(CreateEventStates.waiting_for_correct_option, F.data.startswith("correct_"))
async def process_correct_option(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора правильного ответа"""
    option_id = int(callback.data.split("_")[1])
    await state.update_data(correct_option_id=option_id)

    await callback.message.edit_text(
        "✅ Правильный вариант выбран!\n\n"
        "📅 Теперь введите дату в формате ДД.ММ.ГГГГ"
    )
    await state.set_state(CreateEventStates.waiting_for_date)
    await callback.answer()