from aiogram.types import (KeyboardButton, KeyboardButtonRequestUser,
                           ReplyKeyboardMarkup)
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Инициализируем билдер
kb_builder = ReplyKeyboardBuilder()
# Создаем кнопки
request_user_btn = KeyboardButton(
    text="Выбрать пользователя",
    request_user=KeyboardButtonRequestUser(request_id=42, user_is_premium=False),
)

# Добавляем кнопки в билдер
kb_builder.row(request_user_btn, width=1)
# Создаем объект клавиатуры
partner_keyboard: ReplyKeyboardMarkup = kb_builder.as_markup(resize_keyboard=True)
