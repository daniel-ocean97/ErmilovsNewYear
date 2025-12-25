import os
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from newyear_sheduler import scheduler

other_router = Router()

# ID администратора из переменной окружения (опционально)
ADMIN_ID = os.getenv("ADMIN_ID")
if ADMIN_ID:
    ADMIN_ID = int(ADMIN_ID)


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    if ADMIN_ID:
        return user_id == ADMIN_ID
    return True  # Если ADMIN_ID не задан, разрешаем всем (для разработки)


@other_router.message(Command(commands="test_schedule"))
async def test_schedule_command(message: Message):
    """Тестовая отправка поздравлений"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Эта команда доступна только администратору")
        return
    
    await message.answer("🧪 Запускаю тестовую отправку...")
    try:
        scheduler.is_test_mode = True
        await scheduler.run_test_now()
        await message.answer("✅ Тестовая отправка завершена! Проверьте логи.")
    except Exception as e:
        await message.answer(f"❌ Ошибка при тестовой отправке: {e}")


@other_router.message(Command(commands="schedule_info"))
async def schedule_info_command(message: Message):
    """Информация о планировщике"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Эта команда доступна только администратору")
        return
    
    try:
        info = await scheduler.get_schedule_info()
        text = (
            f"📊 Информация о планировщике:\n\n"
            f"Всего задач: {info['total_tasks']}\n"
            f"Активных задач: {info['active_tasks']}\n"
            f"Тестовый режим: {'Да' if info['is_test_mode'] else 'Нет'}\n"
            f"Текущий год: {info['current_year']}"
        )
        await message.answer(text)
    except Exception as e:
        await message.answer(f"❌ Ошибка при получении информации: {e}")


# Этот хэндлер будет реагировать на любые сообщения пользователя,
# не предусмотренные логикой работы бота
@other_router.message()
async def send_echo(message: Message):
    await message.answer("Я все лишь чат бот и сейчас твоего сообщения не понял(")
