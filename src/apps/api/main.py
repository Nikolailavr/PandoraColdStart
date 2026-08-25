import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

from apps.algoritm import ColdStart
from core.config import settings, bot

logger = logging.getLogger(__name__)

router = APIRouter(tags=["HA Bridge"])

API_KEY = settings.api.key

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(
    header_key: str = Security(api_key_header),
):
    if header_key == API_KEY:
        return True
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN,
        detail="Ошибка авторизации: неверный API ключ",
    )


@router.get("/send", dependencies=[Depends(verify_api_key)])
async def send_command(
    # Теперь 'cmd' имеет дефолтное значение "start".
    # Если HA передаст ?cmd=..., выполнится переданное значение. Если не передаст — будет "start".
    cmd: str = Query(
        default="start", description="Команда для отправки (по умолчанию: start)"
    ),
):
    logger.info(f"Авторизация успешна. Выполняю команду: {cmd}")
    try:
        await ColdStart().begin()
        await bot.send_message(chat_id=settings.telegram.chat_id, text="✅ Процедура холодного запуска завершена.")
    except Exception as e:
        logger.exception("Ошибка при холодном запуске: %s", e)
        await bot.send_message(chat_id=settings.telegram.chat_id, text="⚠️ Произошла ошибка на сервере")

    return {
        "status": "success",
        "message": f"Команда '{cmd}' успешно обработана",
    }