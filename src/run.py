import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

# Импортируем ваш роутер
from apps.api.main import router as ha_bridge_router
from apps.bot.bot_main import start_bot
from apps.utils.schedule import schedule_all_tasks, scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    logger.info("Запускаем расписание")
    scheduler.start()
    schedule_all_tasks()

    logger.info("Запускаем бот-поллинг в фоновой задаче")
    bot_task = asyncio.create_task(start_bot())

    yield

    # SHUTDOWN
    logger.info("Останавливаем расписание и бота")
    scheduler.shutdown(wait=False)

    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        logger.info("Бот успешно остановлен")


app = FastAPI(title="HA to Bot Bridge", lifespan=lifespan)

# Подключаем роуты для Home Assistant
app.include_router(ha_bridge_router)


def main():
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    main()