import asyncio
import logging

from apps.bot.bot_main import start_bot
from apps.utils.schedule import schedule_all_tasks, scheduler

logger = logging.getLogger(__name__)


async def run_all():
    logger.info("Запускаем расписание")
    scheduler.start()
    schedule_all_tasks()
    logger.info("Запускаем бота в основном потоке")
    await start_bot()


def main():
    asyncio.run(run_all())


if __name__ == "__main__":
    main()
