import logging

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apps.bot.handlers import register_all_handlers
from core.config import bot

logger = logging.getLogger(__name__)

dp = Dispatcher(storage=MemoryStorage())


async def start_bot():
    # Регистрация обработчиков
    register_all_handlers(dp)

    # Запуск поллинга
    await dp.start_polling(bot, skip_updates=True)
