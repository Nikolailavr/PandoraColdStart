import json

from core.config import SCHEDULE_FILE


DEFAULT_SCHEDULE = {
    "mon": {"enabled": False, "time": None},
    "tue": {"enabled": False, "time": None},
    "wed": {"enabled": False, "time": None},
    "thu": {"enabled": False, "time": None},
    "fri": {"enabled": False, "time": None},
    "sat": {"enabled": False, "time": None},
    "sun": {"enabled": False, "time": None},
}


def load_schedule() -> dict:
    if not SCHEDULE_FILE.exists():
        return DEFAULT_SCHEDULE.copy()
    with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_schedule(schedule: dict):
    SCHEDULE_FILE.parent.mkdir(exist_ok=True, parents=True)
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)


def get_schedule() -> dict:
    return load_schedule()


def update_schedule(day: str, enabled: bool, time: str | None):
    schedule = load_schedule()
    schedule[day]["enabled"] = enabled
    schedule[day]["time"] = time
    save_schedule(schedule)
