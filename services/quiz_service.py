from aiogram import Bot
from aiogram.types import (
    Message,
    Poll,
    PollAnswer,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from typing import Optional
import asyncio


class QuizService:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def create_quiz(
            self,
            chat_id: int,
            question: str,
            options: list[str],
            correct_option_id: int,
            explanation: str = None,
            photo_file_id: str = None,
            is_anonymous: bool = False,
            open_period: int = 300  # 5 минут на ответ
    ) -> Poll:
        """
        Создать викторину в Telegram
        """
        try:
            # Если есть фото, сначала отправляем его
            if photo_file_id:
                photo_msg = await self.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_file_id,
                    caption="🎬 Вспомни, когда это было?"
                )
                await asyncio.sleep(1)  # Небольшая пауза

            # Создаем викторину (QUIZ - специальный тип с правильным ответом)
            message = await self.bot.send_poll(
                chat_id=chat_id,
                question=question,
                options=options,
                type="quiz",  # Ключевой параметр - это викторина!
                correct_option_id=correct_option_id,
                explanation=explanation,
                is_anonymous=is_anonymous,
                open_period=open_period,
                is_closed=False
            )

            return message.poll

        except Exception as e:
            print(f"Ошибка создания викторины: {e}")
            raise

    async def check_quiz_answer(
            self,
            poll_answer: PollAnswer,
            correct_option_id: int
    ) -> bool:
        """
        Проверить ответ на викторину
        """
        return poll_answer.option_ids[0] == correct_option_id

    async def close_quiz(
            self,
            chat_id: int,
            message_id: int
    ):
        """
        Закрыть викторину
        """
        await self.bot.stop_poll(
            chat_id=chat_id,
            message_id=message_id
        )

    async def create_and_save_quiz(
            self,
            chat_id: int,
            question: str,
            options: list[str],
            correct_option_id: int,
            explanation: str = None,
            photo_file_id: str = None
    ) -> tuple[Poll, int]:
        """
        Создать викторину и вернуть (poll объект, message_id)
        """
        try:
            # Отправляем фото, если есть
            if photo_file_id:
                await self.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_file_id,
                    caption="🎬 Вспомни, когда это было?"
                )
                await asyncio.sleep(1)

            # Создаем викторину
            message = await self.bot.send_poll(
                chat_id=chat_id,
                question=question,
                options=options,
                type="quiz",
                correct_option_id=correct_option_id,
                explanation=explanation,
                is_anonymous=False,  # Видим кто ответил
                open_period=600,  # 10 минут
                is_closed=False
            )

            # Возвращаем poll объект и message_id
            return message.poll, message.message_id

        except Exception as e:
            print(f"Ошибка создания викторины: {e}")
            raise