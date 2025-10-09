import asyncio
import logging

from apps.pandora.base import PandoraBase

logger = logging.getLogger(__name__)


class PandoraState:
    """Объект для хранения состояния Pandora."""

    def __init__(self):
        self.engine_temp = None
        self.out_temp = None
        self.voltage = None
        self.engine_temp_before = None
        self.voltage_before = None
        self.count = None


class Pandora(PandoraBase):
    def __init__(self):
        super().__init__()
        self.state = PandoraState()

    async def start_engine(self):
        if await self._check_auth():
            await self._send_command(4)

    async def stop_engine(self):
        if await self._check_auth():
            await self._send_command(8)

    async def start_heater(self):
        if await self._check_auth():
            await self._send_command(21)

    async def check(self):
        if await self._check_auth():
            await self._send_command(255)
            await asyncio.sleep(3)
            data = await self._get_updates()
            await self._set_params(data)

    async def _set_params(self, data: dict):
        if not self._device_id:
            logger.warning("Device ID не установлен, невозможно обновить параметры")
            return

        stats = data.get("stats", {})
        device_stats = stats.get(str(self._device_id), {})

        # Берём нужные параметры
        self.state.engine_temp = device_stats.get("engine_temp")
        self.state.out_temp = device_stats.get("out_temp")
        self.state.voltage = device_stats.get("voltage")

        logger.debug(
            "Обновлены параметры: engine_temp=%s, out_temp=%s, voltage=%s",
            self.state.engine_temp,
            self.state.out_temp,
            self.state.voltage,
        )


# Пример использования
async def _test():
    async with Pandora() as pandora:
        await pandora.check()


if __name__ == "__main__":
    asyncio.run(_test())
