from aiogram import Dispatcher

from apps.bot.handlers.user import (
    register_users_handlers,
    register_users_settings_handlers,
)


def register_all_handlers(dp: Dispatcher) -> None:
    handlers = (
        register_users_handlers,
        register_users_settings_handlers,
    )
    for handler in handlers:
        handler(dp)
