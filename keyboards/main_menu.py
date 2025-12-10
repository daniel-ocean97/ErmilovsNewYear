from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from lexicon.lexicon import LEXICON_COMMANDS


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает основное меню с командами бота
    """
    builder = ReplyKeyboardBuilder()

    # Добавляем кнопки в меню
    buttons = [
        KeyboardButton(text=LEXICON_COMMANDS["/create_event"]),
        KeyboardButton(text=LEXICON_COMMANDS["/partner"]),
        KeyboardButton(text=LEXICON_COMMANDS["/congratulate"]),
        KeyboardButton(text=LEXICON_COMMANDS["/help"]),
        KeyboardButton(text=LEXICON_COMMANDS["/my_congratulations"]),
    ]

    # Располагаем кнопки по 2 в ряд для красивого вида
    for button in buttons:
        builder.add(button)

    builder.adjust(2, 2, 1)  # Первые 2 ряда по 2 кнопки, последний ряд - 1 кнопка

    return builder.as_markup(resize_keyboard=True)


# Альтернативный вариант с фиксированным расположением
def get_main_menu_simple() -> ReplyKeyboardMarkup:
    """
    Упрощенное меню
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=LEXICON_COMMANDS["/create_event"]),
                KeyboardButton(text=LEXICON_COMMANDS["/partner"]),
            ],
            [
                KeyboardButton(text=LEXICON_COMMANDS["/congratulate"]),
                KeyboardButton(text=LEXICON_COMMANDS["/help"]),
            ],
            [KeyboardButton(text=LEXICON_COMMANDS["/my_congratulations"])],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,  # Меню остается всегда видимым
    )
