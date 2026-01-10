import logging

from aiogram import Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message

from apps.algoritm import ColdStart
from apps.bot.keyboards.main import start_keyboard
from apps.pandora.api import Pandora
from core import settings, tg_msg

router = Router()
logger = logging.getLogger(__name__)


# --- Обработчик команды /start ---
@router.message(Command("start"))
async def cmd_start(msg: Message):
    if msg.from_user.id in settings.telegram.admin_chat_ids:
        await msg.answer(
            "Привет! 👋\nНажми кнопку ниже, чтобы выполнить холодный запуск двигателя.",
            reply_markup=start_keyboard,
        )


@router.message(F.text == "Состояние")
async def __check_car(msg: Message):
    if msg.from_user.id in settings.telegram.admin_chat_ids:
        try:
            pandora = Pandora()
            await pandora.check()
            await tg_msg.msg_params(pandora.state)
        except Exception as e:
            logger.exception("Ошибка при запросе состояния", e)
            await msg.answer("⚠️ Произошла ошибка при запросе состояния.")


# --- Обработчик кнопки ---
@router.message(F.text == "🚗 Старт двигателя")
async def cmd_engine_start(msg: Message):
    if msg.from_user.id in settings.telegram.admin_chat_ids:
        await msg.answer("⏳ Начинаю процедуру холодного запуска...")

        try:
            await ColdStart().begin()
            await msg.answer("✅ Процедура холодного запуска завершена.")
        except Exception as e:
            logger.exception("Ошибка при холодном запуске: %s", e)
            await msg.answer("⚠️ Произошла ошибка на сервере")


@router.message(F.forward_from | F.forward_from_chat)
async def handle_forwarded_message(msg: Message):
    if msg.from_user.id not in settings.telegram.admin_chat_ids:
        return
    # Проверяем, является ли сообщение пересланным
    if msg.forward_from_chat or msg.forward_from:
        response = "📨 Информация о пересланном сообщении:\n\n"

        # Если сообщение переслано из канала/группы
        if msg.forward_from_chat:
            response += f"🆔 ID чата/канала: `{msg.forward_from_chat.id}`\n"
            response += f"📋 Тип: {msg.forward_from_chat.type}\n"
            response += f"🏷️ Название: {msg.forward_from_chat.title}\n"

            # ID оригинального сообщения в том чате/канале
            if msg.forward_from_message_id:
                response += f"💬 ID сообщения в исходном чате: `{msg.forward_from_message_id}`\n"

        # Если сообщение переслано от пользователя
        if msg.forward_from:
            response += f"👤 ID пользователя: `{msg.forward_from.id}`\n"
            response += f"📛 Имя: {msg.forward_from.first_name}\n"
            if msg.forward_from.last_name:
                response += f"📛 Фамилия: {msg.forward_from.last_name}\n"
            if msg.forward_from.username:
                response += f"🔗 Username: @{msg.forward_from.username}\n"

        # ID текущего сообщения
        response += f"\n📝 ID этого сообщения: `{msg.message_id}`"

    else:
        response = "❌ Это не пересланное сообщение"

    await msg.answer(response, parse_mode="Markdown")


def register_users_handlers(dp: Dispatcher) -> None:
    dp.include_router(router)
