"""
Планировщик новогодних поздравлений на asyncio
Отправляет каждое поздравление один раз, обоим партнерам, в случайное время
в диапазоне от 00:00 01.01.2026 до 23:59:59 13.01.2026
"""
import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config.config import load_config
from database.repository import get_all_partner_pairs

logger = logging.getLogger(__name__)


class NewYearScheduler:
    """Планировщик новогодних поздравлений"""

    def __init__(self, bot: Bot = None):
        self.bot = bot
        self.scheduled_tasks: List[asyncio.Task] = []
        self.is_test_mode = False  # Режим для тестов (игнорирует проверку года)

    async def send_single_congratulation(
        self,
        sender_name: str,
        congrat: Dict,
        user1_id: int,
        user2_id: int
    ) -> None:
        """
        Отправка одного поздравления обоим партнерам
        """
        if not self.bot:
            cfg = load_config()
            self.bot = Bot(
                token=cfg.bot.token,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )

        # Функция для отправки одного сообщения
        async def send_message(recipient_id: int):
            try:
                if congrat.get("photo_file_id"):
                    await self.bot.send_photo(
                        chat_id=recipient_id,
                        photo=congrat["photo_file_id"],
                        caption=f"👤 От {sender_name}:\n{congrat['message']}"
                    )
                else:
                    await self.bot.send_message(
                        chat_id=recipient_id,
                        text=f"👤 От {sender_name}:\n{congrat['message']}"
                    )
                await asyncio.sleep(0.04)  # Rate limiting: ~25 сообщений/сек
            except Exception as e:
                logger.error(f"Ошибка отправки {sender_name} → {recipient_id}: {e}")

        # Отправляем обоим партнерам
        await send_message(user1_id)
        await send_message(user2_id)

        logger.debug(f"✅ Отправлено поздравление от {sender_name} обоим партнерам")

    async def schedule_congratulation(
        self,
        sender_name: str,
        congrat: Dict,
        user1_id: int,
        user2_id: int,
        send_time: datetime
    ) -> None:
        """
        Запланировать отправку одного поздравления на конкретное время
        """
        async def scheduled_send():
            # Вычисляем сколько ждать до отправки
            now = datetime.now()
            if send_time > now:
                wait_seconds = (send_time - now).total_seconds()
                if wait_seconds > 0:
                    logger.debug(f"⏳ Ожидание {wait_seconds:.0f} сек для отправки поздравления от {sender_name}")
                    await asyncio.sleep(wait_seconds)

            # Отправляем
            logger.info(f"🎉 Отправка поздравления от {sender_name}")
            await self.send_single_congratulation(sender_name, congrat, user1_id, user2_id)

        # Создаем и сохраняем задачу
        task = asyncio.create_task(scheduled_send())
        self.scheduled_tasks.append(task)
        return task

    async def schedule_all_congratulations(self) -> None:
        """
        Основная функция планирования всех поздравлений
        Каждое поздравление отправляется один раз, обоим партнерам, в случайное время
        """
        # Проверяем год (если не в тестовом режиме)
        current_year = datetime.now().year
        if not self.is_test_mode and current_year != 2026:
            logger.info(f"⏸️ Пропускаем планирование. Текущий год: {current_year}, "
                       f"ожидается 2026. Планировщик будет ждать.")
            return

        # Получаем все пары из базы
        pairs = await get_all_partner_pairs()
        if not pairs:
            logger.info("📭 Нет пар партнеров для отправки поздравлений")
            return

        logger.info(f"📅 Начинаем планирование для {len(pairs)} пар")

        # Определяем временные границы
        now = datetime.now()
        if self.is_test_mode:
            # Для тестов: начинаем через 60 секунд, заканчиваем через 2 дня
            start_time = datetime.now() + timedelta(seconds=60)
            end_date = start_time + timedelta(days=2)
            logger.info("🔬 ТЕСТОВЫЙ РЕЖИМ: отправка начнется через 60 секунд")
        else:
            # Для продакшена: 00:00 01.01.2026 - 23:59:59 13.01.2026
            original_start_time = datetime(2026, 1, 1, 0, 0, 0)
            end_date = datetime(2026, 1, 13, 23, 59, 59)
            
            # Если start_time уже прошло, начинаем с текущего момента
            if now > original_start_time:
                if now > end_date:
                    # Если мы уже после end_date - отправляем все сразу
                    logger.warning(f"⚠️ Период рассылки уже прошел (до {end_date}), отправляем все поздравления немедленно")
                    start_time = now
                    end_date = now + timedelta(minutes=5)  # Распределим на 5 минут
                else:
                    # Если мы в периоде, но после start_time - начинаем с текущего момента
                    start_time = now
                    logger.info(f"⏰ Период рассылки начался ({original_start_time}), но бот запущен позже. Начинаем с текущего момента до {end_date}")
            else:
                start_time = original_start_time
                logger.info(f"🎯 ПРОДАКШЕН: отправка с {start_time} по {end_date}")

        # Собираем все поздравления и планируем каждое отдельно
        all_congratulations = []
        total_congrats = 0

        for pair in pairs:
            user1 = pair["user1"]
            user2 = pair["user2"]
            user1_id = user1["telegram_id"]
            user2_id = user2["telegram_id"]

            # Добавляем поздравления от user1
            for congrat in user1["congratulations"]:
                all_congratulations.append({
                    "sender_name": user1["first_name"],
                    "congrat": congrat,
                    "user1_id": user1_id,
                    "user2_id": user2_id
                })
                total_congrats += 1

            # Добавляем поздравления от user2
            for congrat in user2["congratulations"]:
                all_congratulations.append({
                    "sender_name": user2["first_name"],
                    "congrat": congrat,
                    "user1_id": user1_id,
                    "user2_id": user2_id
                })
                total_congrats += 1

        if not all_congratulations:
            logger.info("📭 Нет поздравлений для отправки")
            return

        logger.info(f"📝 Найдено {total_congrats} поздравлений для планирования")

        if total_congrats == 0:
            logger.warning("Нет поздравлений для планирования")
            return

        # Перемешиваем для случайного распределения во времени
        random.shuffle(all_congratulations)

        # Вычисляем оставшееся время
        now = datetime.now()
        remaining_time_range = int((end_date - start_time).total_seconds())
        
        # Если времени осталось мало (меньше 1 минуты) или уже прошло - отправляем все сразу с небольшими задержками
        if remaining_time_range <= 60 or now >= end_date:
            logger.info(f"⚡ Времени осталось мало ({remaining_time_range} сек) или период прошел. Отправляем все поздравления с небольшими задержками")
            for i, item in enumerate(all_congratulations):
                # Небольшая задержка между отправками (1-2 секунды)
                send_time = now + timedelta(seconds=i * 1.5)
                await self.schedule_congratulation(
                    sender_name=item["sender_name"],
                    congrat=item["congrat"],
                    user1_id=item["user1_id"],
                    user2_id=item["user2_id"],
                    send_time=send_time
                )
        else:
            # Первое поздравление в start_time (или сейчас, если start_time в прошлом)
            first_item = all_congratulations[0]
            first_send_time = max(start_time, now)
            await self.schedule_congratulation(
                sender_name=first_item["sender_name"],
                congrat=first_item["congrat"],
                user1_id=first_item["user1_id"],
                user2_id=first_item["user2_id"],
                send_time=first_send_time
            )
            logger.info(f"⏰ Первое поздравление запланировано на {first_send_time}")

            # Остальные поздравления распределяем случайно по оставшемуся времени
            if total_congrats > 1:
                # Время начинается с 1 минуты после start_time (или сейчас, если start_time в прошлом)
                remaining_start = max(start_time + timedelta(seconds=60), now)
                remaining_time_range = int((end_date - remaining_start).total_seconds())
                
                # Если времени осталось очень мало, отправляем с небольшими задержками
                if remaining_time_range <= 0:
                    remaining_start = now
                    remaining_time_range = 60  # Минимум 1 минута для распределения

                # Равномерно распределяем оставшиеся поздравления
                remaining_congrats = total_congrats - 1
                step = remaining_time_range / max(1, remaining_congrats - 1) if remaining_congrats > 1 else remaining_time_range

                for i, item in enumerate(all_congratulations[1:], start=1):
                    # Базовое время - равномерное распределение
                    base_offset = (i - 1) * step

                    # Добавляем случайное отклонение (±10% от шага)
                    random_deviation = random.uniform(-step * 0.1, step * 0.1)
                    total_offset = base_offset + random_deviation

                    # Убеждаемся, что offset в допустимых пределах
                    total_offset = max(0, min(total_offset, remaining_time_range))

                    send_time = remaining_start + timedelta(seconds=int(total_offset))

                    # Убеждаемся, что время не выходит за границы и не в прошлом
                    if send_time > end_date:
                        send_time = end_date
                    if send_time < now:
                        send_time = now + timedelta(seconds=i * 1.5)  # Минимальная задержка

                    await self.schedule_congratulation(
                        sender_name=item["sender_name"],
                        congrat=item["congrat"],
                        user1_id=item["user1_id"],
                        user2_id=item["user2_id"],
                        send_time=send_time
                    )

        logger.info(f"✅ Запланировано {total_congrats} поздравлений для {len(pairs)} пар")

    async def run_test_now(self) -> None:
        """
        Немедленный тест отправки (без планирования)
        Отправляет все поздравления сразу для тестирования
        """
        logger.info("🧪 ЗАПУСК ТЕСТА ОТПРАВКИ")

        pairs = await get_all_partner_pairs()
        if not pairs:
            logger.warning("Нет пар для теста")
            return

        logger.info(f"Тестируем отправку для {len(pairs)} пар")

        total_sent = 0
        for pair in pairs:
            user1 = pair["user1"]
            user2 = pair["user2"]
            user1_id = user1["telegram_id"]
            user2_id = user2["telegram_id"]

            # Отправляем все поздравления от user1
            for congrat in user1["congratulations"]:
                await self.send_single_congratulation(
                    sender_name=user1["first_name"],
                    congrat=congrat,
                    user1_id=user1_id,
                    user2_id=user2_id
                )
                total_sent += 1
                await asyncio.sleep(0.1)  # Небольшая пауза между отправками

            # Отправляем все поздравления от user2
            for congrat in user2["congratulations"]:
                await self.send_single_congratulation(
                    sender_name=user2["first_name"],
                    congrat=congrat,
                    user1_id=user1_id,
                    user2_id=user2_id
                )
                total_sent += 1
                await asyncio.sleep(0.1)  # Небольшая пауза между отправками

        logger.info(f"✅ ТЕСТ ЗАВЕРШЕН. Отправлено {total_sent} поздравлений")

    async def get_schedule_info(self) -> Dict:
        """
        Возвращает информацию о запланированных задачах
        """
        return {
            "total_tasks": len(self.scheduled_tasks),
            "active_tasks": sum(1 for t in self.scheduled_tasks if not t.done()),
            "is_test_mode": self.is_test_mode,
            "current_year": datetime.now().year,
        }

    async def cleanup(self) -> None:
        """
        Очистка ресурсов и отмена всех задач
        """
        # Отменяем все запланированные задачи
        for task in self.scheduled_tasks:
            if not task.done():
                task.cancel()

        # Закрываем сессию бота
        if self.bot:
            await self.bot.session.close()

        logger.info("Планировщик остановлен, ресурсы очищены")


# Глобальный экземпляр планировщика
scheduler = NewYearScheduler()


async def init_scheduler(bot: Bot = None) -> NewYearScheduler:
    """
    Инициализация планировщика при запуске бота
    """
    if bot:
        scheduler.bot = bot

    # Запускаем планирование
    await scheduler.schedule_all_congratulations()

    return scheduler