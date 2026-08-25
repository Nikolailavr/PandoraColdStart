from fastapi import APIRouter, Depends, HTTPException, Query, Security
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

from core.config import settings

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
async def send_command(cmd: str = Query(..., description="Команда для отправки")):
    print(f"Авторизация успешна. Выполняю команду: {cmd}")

    return {
        "status": "success",
        "message": f"Команда '{cmd}' успешно обработана",
    }