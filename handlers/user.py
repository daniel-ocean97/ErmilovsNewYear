from copy import deepcopy

from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message
from keyboards.add_patrner import partner_keyboard
from lexicon.lexicon import LEXICON

user_router = Router()

@user_router.message(CommandStart())
async def process_start_command(message: Message, db: dict):
    text = LEXICON[message.text]
    await message.answer(text=text)
    if message.from_user.id not in db["users"]:
        db["users"].append({'id': deepcopy(message.from_user.id), 'partner': None, 'game_files': None})


@user_router.message(Command(commands="help"))
async def process_help_command(message: Message):
    await message.answer(LEXICON[message.text])


@user_router.message(Command(commands="partner"))
async def process_partner_command(message: Message):
    await message.answer(text='Выбери своего партнера', reply_markup=partner_keyboard)

# Этот хэндлер будет срабатывать на выбор пользователя из списка
@user_router.message(F.user_shared)
async def process_user_shared(message: Message, db: dict):
    print(message.model_dump_json(indent=4, exclude_none=True))
    for user in db['users']:
        if message.from_user.id == user['id']:
            user['partner'] = message.user_shared.user_id
    await message.answer(text='ух, кайф) записал как твоего партнера', reply_markup=types.ReplyKeyboardRemove())



