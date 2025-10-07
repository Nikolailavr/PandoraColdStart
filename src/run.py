import asyncio
import logging

from apps.bot.bot_main import start_bot

logger = logging.getLogger(__name__)


def main():
    # Запускаем бота в основном потоке
    logger.info("Запускаем бота в основном потоке")
    asyncio.run(start_bot())


if __name__ == "__main__":
    main()
