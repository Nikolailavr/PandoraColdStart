import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pathlib import Path
import json

from apps.algoritm import ColdStart

logger = logging.getLogger(__name__)

# --- Настройки ---
SCHEDULE_FILE = Path("/src/data/schedule.json")  # путь к JSON с расписанием

scheduler = AsyncIOScheduler()
scheduler.start()


# --- Вспомогательные функции ---
def load_schedule() -> dict:
    """Загружает расписание из JSON"""
    if not SCHEDULE_FILE.exists():
        return {
            "mon": {"enabled": False, "time": None},
            "tue": {"enabled": False, "time": None},
            "wed": {"enabled": False, "time": None},
            "thu": {"enabled": False, "time": None},
            "fri": {"enabled": False, "time": None},
            "sat": {"enabled": False, "time": None},
            "sun": {"enabled": False, "time": None},
        }
    with SCHEDULE_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_schedule(schedule: dict):
    """Сохраняет расписание в JSON"""
    SCHEDULE_FILE.parent.mkdir(exist_ok=True)
    with SCHEDULE_FILE.open("w", encoding="utf-8") as f:
        json.dump(schedule, f, indent=4, ensure_ascii=False)


# --- ColdStart задача ---
async def run_cold_start():
    logger.info("Запуск ColdStart по расписанию")
    cs = ColdStart()
    await cs.begin()


# --- Планирование задач ---
def schedule_all_tasks():
    """Создаёт или обновляет все задачи планировщика на основании JSON"""
    schedule = load_schedule()

    for day, data in schedule.items():
        job_id = f"cold_start_{day}"

        # Удаляем старую задачу
        try:
            scheduler.remove_job(job_id)
            logger.info(f"Старая задача {job_id} удалена")
        except Exception:
            pass

        # Добавляем новую задачу, если день включён
        if data.get("enabled") and data.get("time"):
            hour, minute = map(int, data["time"].split(":"))
            scheduler.add_job(
                lambda: asyncio.create_task(run_cold_start()),
                "cron",
                day_of_week=day[:3],  # 'mon', 'tue', ...
                hour=hour,
                minute=minute,
                id=job_id,
                replace_existing=True,
            )
            logger.info(f"Задача на {day} {data['time']} добавлена")


# --- Обновление конкретного дня (например, после изменения пользователем) ---
def update_task(day: str, enabled: bool = None, time: str = None):
    """Обновляет задачу для конкретного дня и сохраняет в JSON"""
    schedule = load_schedule()
    if enabled is not None:
        schedule[day]["enabled"] = enabled
    if time is not None:
        schedule[day]["time"] = time
    save_schedule(schedule)
    schedule_all_tasks()  # пересоздаём задачи
