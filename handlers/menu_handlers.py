# from aiogram import Router, types
# from aiogram.filters import Command
# from keyboards.main_menu import get_main_menu_keyboard
#
# menu_router = Router()
#
#
# @menu_router.message(Command("menu"))
# async def show_main_menu(message: types.Message):
#     """
#     Показывает главное меню с кнопками
#     """
#     await message.answer(
#         "🎄 <b>Главное меню</b>\n\n"
#         "Выбери действие:",
#         reply_markup=get_main_menu_keyboard(),
#         parse_mode="HTML"
#     )
#
#
# @menu_router.message(lambda message: message.text in [
#     "🎮 Создать воспоминание",
#     "👫 Выбрать партнёра",
#     "💌 Написать поздравление",
#     "📖 Правила игры",
#     "📦 Мои поздравления"
# ])
# async def handle_menu_button(message: types.Message):
#     """
#     Обрабатывает нажатия кнопок меню
#     """
#     text = message.text
#
#     if text == "🎮 Создать воспоминание":
#         await message.answer(
#             "Для создания воспоминания используй команду:\n"
#             "<code>/create_event</code>",
#             parse_mode="HTML"
#         )
#
#     elif text == "👫 Выбрать партнёра":
#         await message.answer(
#             "Для выбора партнёра используй команду:\n"
#             "<code>/partner</code>",
#             parse_mode="HTML"
#         )
#
#     elif text == "💌 Написать поздравление":
#         await message.answer(
#             "Для написания поздравления используй команду:\n"
#             "<code>/congratulate</code>",
#             parse_mode="HTML"
#         )
#
#     elif text == "📖 Правила игры":
#         from lexicon.lexicon import LEXICON
#         await message.answer(
#             LEXICON["/help"],
#             parse_mode="HTML"
#         )
#
#     elif text == "📦 Мои поздравления":
#         await message.answer(
#             "Для просмотра поздравлений используй команду:\n"
#             "<code>/my_congratulations</code>",
#             parse_mode="HTML"
#         )