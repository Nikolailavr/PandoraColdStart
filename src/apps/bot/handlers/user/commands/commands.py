import logging

from aiogram import Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message

from apps.algoritm import ColdStart
from apps.bot.handlers.user.keyboards.main import start_keyboard

router = Router()
logger = logging.getLogger(__name__)


# --- Обработчик команды /start ---
@router.message(Command("start"))
async def cmd_start(msg: Message):
    await msg.answer(
        "Привет! 👋\nНажми кнопку ниже, чтобы выполнить холодный запуск двигателя.",
        reply_markup=start_keyboard,
    )


# --- Обработчик кнопки ---
@router.message(F.text == "🚗 Старт двигателя")
async def cmd_engine_start(msg: Message):
    await msg.answer("⏳ Начинаю процедуру холодного запуска...")

    try:
        await ColdStart().begin()
        await msg.answer("✅ Процедура холодного запуска завершена.")
    except Exception as e:
        logger.exception("Ошибка при холодном запуске: %s", e)
        await msg.answer("⚠️ Произошла ошибка при запуске двигателя.")


def register_users_handlers(dp: Dispatcher) -> None:
    dp.include_router(router)
