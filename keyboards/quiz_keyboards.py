from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)


def get_event_keyboard():
    """
    Клавиатура для создания ивента
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📸 Создать воспоминание")],
            [
                KeyboardButton(text="📊 Мои ивенты"),
                KeyboardButton(text="🏆 Статистика"),
            ],
            [KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True,
    )


def get_congratulation_keyboard(event_id: int):
    """
    Клавиатура для поздравления
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎉 Написать поздравление",
                    callback_data=f"congratulate_{event_id}",
                )
            ]
        ]
    )
