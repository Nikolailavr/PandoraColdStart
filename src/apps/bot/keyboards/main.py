from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🚗 Старт двигателя"),
            KeyboardButton(text="Состояние"),
            KeyboardButton(text="🕒 Расписание"),
        ],
    ],
    resize_keyboard=True,
)
