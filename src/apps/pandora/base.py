import asyncio
import logging
import aiohttp
from typing import Optional, Dict, Any
from core import settings

logger = logging.getLogger(__name__)


class PandoraBase:
    __BASE_URL = "https://p-on.ru/api"

    __BASE_HEADERS = {
        "sec-ch-ua-platform": '"Windows"',
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "sec-ch-ua-mobile": "?0",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Origin": "https://p-on.ru",
        "Referer": "https://p-on.ru/",
        "Connection": "keep-alive",
    }

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._cookies: Dict[str, str] = {}
        self._login_name = settings.pandora.login
        self._password = settings.pandora.password
        self._device_id: Optional[int] = None  # ID устройства для команд
        self._auth_ok = False

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def _ensure_session(self):
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()

    async def _login(self) -> Dict[str, Any]:
        """Авторизация в Pandora API и сохранение cookies sid/lang."""
        await self._ensure_session()
        url = f"{self.__BASE_URL}/users/login"
        data = {
            "lang": "ru",
            "login": self._login_name,
            "password": self._password,
        }
        headers = self.__BASE_HEADERS

        async with self._session.post(
            url,
            data=data,
            headers=headers,
        ) as resp:
            text = await resp.text()
            try:
                result = await resp.json()
            except Exception:
                logger.error("Login response not JSON: %s", text)
                raise

            if resp.status != 200 or result.get("status") != "success":
                logger.error("Login failed [%s]: %s", resp.status, result)
                raise aiohttp.ClientResponseError(
                    status=resp.status,
                    request_info=resp.request_info,
                    history=resp.history,
                    message=str(result),
                )

            session_id = result.get("session_id")
            lang_value = result.get("lang", "ru")

            if session_id:
                self._cookies["sid"] = session_id
                self._cookies["lang"] = lang_value
                logger.debug(
                    "Авторизация успешна: sid=%s, lang=%s", session_id, lang_value
                )
                await self._fetch_devices()
            else:
                logger.warning("Ответ без session_id: %s", result)

            return result

    async def _fetch_devices(self) -> None:
        """Получает список устройств и сохраняет device_id первого авто."""
        devices = await self._request("GET", "/devices")
        if not devices or not isinstance(devices, list):
            logger.warning("Список устройств пуст или некорректный: %s", devices)
            return
        self._device_id = devices[0].get("id")
        logger.debug("Сохранён device_id: %s", self._device_id)
        self._auth_ok = True

    async def _send_command(self, command: int) -> Dict[str, Any]:
        """Отправка команды устройству по device_id."""
        if not self._device_id:
            raise ValueError(
                "Device ID не установлен. Выполните fetch_devices() или login() сначала."
            )
        data = {"command": command, "id": self._device_id}
        result = await self._request("POST", "/devices/command", data=data)
        logger.debug("Команда %s отправлена: %s", command, result)
        return result

    async def _is_alive(self) -> bool:
        """Проверяет, активна ли текущая сессия (POST /api/iamalive)."""
        await self._ensure_session()
        url = f"{self.__BASE_URL}/iamalive"
        data = {"num_click": 0}
        cookies = self._cookies or {}
        headers = self.__BASE_HEADERS

        async with self._session.post(
            url,
            data=data,
            cookies=cookies,
            headers=headers,
        ) as resp:
            try:
                result = await resp.json()
            except Exception:
                text = await resp.text()
                logger.error("Invalid response from iamalive: %s", text)
                return False

            status = result.get("status")
            if status == "you are alive":
                logger.debug("Сессия активна.")
                return True
            elif status == "sid-expired":
                logger.warning("Сессия истекла, требуется повторный логин.")
                return False
            else:
                logger.warning("Неизвестный статус проверки: %s", status)
                return False

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        retries: int = 3,
    ) -> Dict[str, Any]:
        """Запрос к Pandora API с авторизацией и повтором при временных ошибках."""
        await self._ensure_session()

        for attempt in range(1, retries + 2):  # 1 основная + N повторов
            # Проверяем валидность сессии
            if not self._cookies or not await self._is_alive():
                logger.debug("Сессия недействительна — логинимся заново")
                await self._login_name()

            url = f"{self.__BASE_URL.rstrip('/')}/{path.lstrip('/')}"

            try:
                async with self._session.request(
                    method.upper(),
                    url,
                    json=json_data,
                    data=data,
                    params=params,
                    cookies=self._cookies,
                    headers=self.__BASE_HEADERS,
                ) as resp:
                    text = await resp.text()
                    try:
                        result = await resp.json()
                    except Exception:
                        logger.error("Ответ не JSON (%s): %s", resp.status, text)
                        raise

                    # --- Обработка ошибок ---
                    if resp.status >= 400 or (
                        isinstance(result, dict) and result.get("status") == "fail"
                    ):
                        logger.warning(
                            "Ошибка запроса (%s %s): %s — попытка %d/%d",
                            method,
                            url,
                            result,
                            attempt,
                            retries + 1,
                        )

                        # 1️⃣ Ошибка сессии
                        if isinstance(result, dict) and result.get("status") in {
                            "sid-expired",
                            "invalid session id",
                        }:
                            await self._login_name()
                            if attempt <= retries:
                                await asyncio.sleep(1)
                                continue

                        # 2️⃣ Ошибка GSM (временная) — повтор через 5 сек
                        if (
                            isinstance(result, dict)
                            and result.get("error_text") == "GSM is unreachable"
                        ):
                            if attempt <= retries:
                                logger.info("GSM недоступен — повтор через 5 секунд...")
                                await asyncio.sleep(5)
                                continue

                        # 3️⃣ Серверная ошибка (5xx) — повтор через 2 сек
                        if 500 <= resp.status < 600 and attempt <= retries:
                            await asyncio.sleep(2)
                            continue

                        # 4️⃣ Ошибка клиента (400) — повтор через 5 сек
                        if resp.status == 400 and attempt <= retries:
                            logger.info("Ошибка 400 — пробуем снова через 5 секунд...")
                            await asyncio.sleep(5)
                            continue

                        # Если все попытки исчерпаны
                        raise aiohttp.ClientResponseError(
                            request_info=resp.request_info,
                            history=resp.history,
                            status=resp.status,
                            message=str(result),
                        )

                    return result  # успешный ответ

            except aiohttp.ClientError as e:
                logger.warning(
                    "Ошибка соединения: %s (попытка %d/%d)", e, attempt, retries + 1
                )
                if attempt <= retries:
                    await asyncio.sleep(2)
                    continue
                raise

        raise RuntimeError("Не удалось выполнить запрос после всех попыток")

    async def _check_auth(self):
        self._auth_ok = await self._is_alive()
        if not self._auth_ok:
            await self._login()
        return self._auth_ok

    async def _get_updates(self) -> Dict[str, Any]:
        """
        Получает обновления Pandora API.
        Запрос: GET /updates?ts=-1
        """
        params = {"ts": "-1"}
        result = await self._request("GET", "/updates", params=params)
        logger.debug("Получены обновления: %s", result)
        return result
