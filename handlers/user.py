from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository import UserRepository, CongratulationRepository
from keyboards.add_patrner import partner_keyboard
from lexicon.lexicon import LEXICON
from datetime import datetime

user_router = Router()


@user_router.message(CommandStart())
async def process_start_command(message: Message, session: AsyncSession):
    # 1. Работа с базой данных
    user_repo = UserRepository(session)
    user = await user_repo.get_user(message.from_user.id)

    if not user:
        # Создаем нового пользователя
        await user_repo.create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        # Отправляем сообщение о регистрации
        await message.answer("🎉 Вы успешно зарегистрированы!")
    else:
        # Пользователь уже зарегистрирован
        await message.answer("👋 С возвращением!")

    # 2. Отправляем ТОЛЬКО приветственное сообщение БЕЗ клавиатуры
    text = LEXICON["/start"]

    await message.answer(
        text=text,
        parse_mode="HTML"
    )


@user_router.message(Command(commands="help"))
async def process_help_command(message: Message):
    await message.answer(LEXICON["/help"], parse_mode="HTML")


@user_router.message(Command(commands="partner"))
async def process_partner_command(message: Message, session: AsyncSession):
    user_repo = UserRepository(session)
    user = await user_repo.get_user(message.from_user.id)

    if not user:
        await message.answer("Сначала зарегистрируйся с помощью /start")
        return

    if user.partner_id:
        partner = await user_repo.get_partner(message.from_user.id)
        await message.answer(f"Ваш партнер уже выбран: {partner.first_name}")
    else:
        await message.answer(text='Выбери своего партнера', reply_markup=partner_keyboard)


@user_router.message(F.user_shared)
async def process_user_shared(message: Message, session: AsyncSession):
    print(message.model_dump_json(indent=4, exclude_none=True))

    user_repo = UserRepository(session)

    # Устанавливаем партнера
    success = await user_repo.set_partner(
        user_id=message.from_user.id,
        partner_telegram_id=message.user_shared.user_id
    )

    if success:
        await message.answer(
            text='Отлично! Партнер сохранен в базе данных 🎯',
            reply_markup=types.ReplyKeyboardRemove()
        )

        # Отправляем приглашение партнеру
        try:
            await message.bot.send_message(
                chat_id=message.user_shared.user_id,
                text=f"🎉 {message.from_user.first_name} выбрал(а) вас своим партнером "
                     f"для подведения итогов года! Для начала приключения используй /start"
            )
        except Exception as e:
            print(f"Не удалось отправить сообщение партнеру: {e}")
    else:
        await message.answer(
            text='Партнер не найден в базе данных. Попросите его начать с /start',
            reply_markup=types.ReplyKeyboardRemove()
        )


@user_router.message(Command(commands="my_congratulations"))
async def process_my_congratulations(message: Message, session: AsyncSession):
    """Показать все собственные поздравления пользователя"""
    user_repo = UserRepository(session)
    user = await user_repo.get_user(message.from_user.id)

    if not user:
        await message.answer("Сначала зарегистрируйся с помощью /start")
        return

    congr_repo = CongratulationRepository(session)
    congrats = await congr_repo.list_by_sender(user.id)

    if not congrats:
        await message.answer("У тебя пока нет поздравлений. Добавь первое через /congratulate")
        return

    lines = []
    for idx, congrat in enumerate(congrats, start=1):
        created = congrat.created_at.strftime("%d.%m.%Y %H:%M") if isinstance(congrat.created_at, datetime) else ""
        suffix = " (с фото)" if congrat.photo_file_id else ""
        lines.append(f"{idx}. {congrat.message}{suffix}{f' — {created}' if created else ''}")

    await message.answer(
        "📦 Твои поздравления:\n\n" + "\n\n".join(lines)
    )