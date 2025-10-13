from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def schedule_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Пн", callback_data="sch_day_mon"),
                InlineKeyboardButton(text="Вт", callback_data="sch_day_tue"),
                InlineKeyboardButton(text="Ср", callback_data="sch_day_wed"),
            ],
            [
                InlineKeyboardButton(text="Чт", callback_data="sch_day_thu"),
                InlineKeyboardButton(text="Пт", callback_data="sch_day_fri"),
            ],
            [
                InlineKeyboardButton(text="Сб", callback_data="sch_day_sat"),
                InlineKeyboardButton(text="Вс", callback_data="sch_day_sun"),
            ],
        ]
    )
