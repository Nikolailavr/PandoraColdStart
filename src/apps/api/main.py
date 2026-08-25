import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Security
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

from apps.pandora.api import Pandora
from core import tg_msg
from core.config import settings

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
    print(f"Авторизация успешна. Выполняю команду: {cmd}")
    try:
        pandora = Pandora()
        await pandora.check()
        await tg_msg.msg_params(pandora.state)
    except Exception as e:
        logger.exception("Ошибка при запросе состояния", e)

    return {
        "status": "success",
        "message": f"Команда '{cmd}' успешно обработана",
    }