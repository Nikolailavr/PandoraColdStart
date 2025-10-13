import re
import logging
from aiogram import Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from apps.bot.keyboards.schedule.day import schedule_day_kb
from apps.bot.keyboards.schedule.main import schedule_main_kb
from apps.utils.schedule import update_task
from apps.utils.storage import get_schedule, update_schedule  # изменено

logger = logging.getLogger(__name__)
router = Router()

# Для русских названий дней
DAY_NAMES = {
    "mon": "Понедельник",
    "tue": "Вторник",
    "wed": "Среда",
    "thu": "Четверг",
    "fri": "Пятница",
    "sat": "Суббота",
    "sun": "Воскресенье",
}


# --- FSM для ввода времени ---
class ScheduleEditTime(StatesGroup):
    waiting_time = State()


# --- Команда /schedule ---
@router.message(Command("schedule"))
async def cmd_schedule(msg: Message):
    await show_schedule(msg)


# --- Кнопка "🕒 Расписание" ---
@router.message(F.text == "🕒 Расписание")
async def on_schedule_button(msg: Message):
    await show_schedule(msg)


# --- Общая функция вывода расписания ---
async def show_schedule(msg: Message):
    schedule = get_schedule()
    text = format_schedule_table(schedule)
    await msg.answer(text, reply_markup=schedule_main_kb(), parse_mode="Markdown")


def format_schedule_table(schedule: dict) -> str:
    lines = [
        "📅 *Текущее расписание:*\n",
        "```",
        f"{'День':<14} | {'Время':<5} | Статус",
        "-" * 28,
    ]

    for day, data in schedule.items():
        time = data.get("time") or "—"
        status = "✅" if data.get("enabled") else "❌"
        lines.append(f"{DAY_NAMES[day]:<14} | {time:<5} | {status}")

    lines.append("```")
    return "\n".join(lines)


# --- Обработка выбора дня недели ---
@router.callback_query(F.data.startswith("sch_day_"))
async def cb_show_day(call: CallbackQuery):
    day = call.data.split("_")[-1]
    schedule = get_schedule()
    day_data = schedule.get(day, {"enabled": False, "time": None})

    enabled = day_data["enabled"]
    time = day_data["time"] or "—"

    text = (
        f"🗓 *{DAY_NAMES[day]}*\n"
        f"Статус: {'✅ Включено' if enabled else '❌ Выключено'}\n"
        f"Время запуска: {time}"
    )

    await call.message.edit_text(
        text, reply_markup=schedule_day_kb(day, enabled), parse_mode="Markdown"
    )


# --- Переключение состояния дня (вкл/выкл) ---
@router.callback_query(F.data.startswith("sch_toggle_"))
async def cb_toggle_day(call: CallbackQuery):
    day = call.data.split("_")[-1]
    schedule = get_schedule()
    new_enabled = not schedule[day]["enabled"]

    # Обновляем глобальное расписание и пересоздаём задачу
    update_schedule(day, enabled=new_enabled, time=schedule[day]["time"])
    update_task(day, enabled=new_enabled, time=schedule[day]["time"])

    time_display = schedule[day]["time"] or "—"
    text = (
        f"🗓 *{DAY_NAMES[day]}*\n"
        f"Статус: {'✅ Включено' if new_enabled else '❌ Выключено'}\n"
        f"Время запуска: {time_display}"
    )

    await call.message.edit_text(
        text, reply_markup=schedule_day_kb(day, new_enabled), parse_mode="Markdown"
    )
    await call.answer("Изменено")


# --- Изменение времени ---
@router.callback_query(F.data.startswith("sch_edit_"))
async def cb_edit_time(call: CallbackQuery, state: FSMContext):
    day = call.data.split("_")[-1]
    await state.set_state(ScheduleEditTime.waiting_time)
    await state.update_data(day=day)
    await call.message.answer(
        f"Введите новое время запуска для *{DAY_NAMES[day]}* в формате `ЧЧ:ММ`",
        parse_mode="Markdown",
    )
    await call.answer()


# --- Получение нового времени ---
@router.message(ScheduleEditTime.waiting_time)
async def msg_set_time(msg: Message, state: FSMContext):
    time_str = msg.text.strip()

    # Проверяем формат времени
    if not re.match(r"^(?:[01]\d|2[0-3]):[0-5]\d$", time_str):
        await msg.answer("⚠️ Некорректный формат. Введите время в виде `07:30`")
        return

    data = await state.get_data()
    day = data["day"]

    # Обновляем глобальное расписание и пересоздаём задачу
    update_schedule(day, enabled=True, time=time_str)
    update_task(day, enabled=True, time=time_str)

    await msg.answer(
        f"✅ Время для *{DAY_NAMES[day]}* установлено: `{time_str}`",
        parse_mode="Markdown",
    )
    await state.clear()


# --- Возврат к списку дней ---
@router.callback_query(F.data == "sch_back_days")
async def cb_back_days(call: CallbackQuery):
    schedule = get_schedule()

    # Формируем таблицу
    text = format_schedule_table(schedule)

    # Обновляем сообщение
    await call.message.edit_text(
        text, reply_markup=schedule_main_kb(), parse_mode="Markdown"
    )
    await call.answer()


def register_users_settings_handlers(dp: Dispatcher) -> None:
    dp.include_router(router)
