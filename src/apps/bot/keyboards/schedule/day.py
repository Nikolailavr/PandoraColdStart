from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def schedule_day_kb(day: str, enabled: bool) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Изменить время", callback_data=f"sch_edit_{day}")],
        [
            InlineKeyboardButton(
                text="Отключить" if enabled else "Включить",
                callback_data=f"sch_toggle_{day}",
            )
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="sch_back_days")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
