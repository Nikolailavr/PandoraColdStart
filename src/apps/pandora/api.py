import asyncio
import logging

from apps.pandora.base import PandoraBase

logger = logging.getLogger(__name__)


class Pandora(PandoraBase):

    def __init__(self):
        super().__init__()
        self.engine_temp_before = None
        self.voltage_before = None
        self.engine_temp = None
        self.out_temp = None
        self.voltage = None

    async def start_engine(self):
        if await self._check_auth():
            await self._send_command(4)

    async def stop_engine(self):
        if await self._check_auth():
            await self._send_command(8)

    async def heater_on(self):
        if await self._check_auth():
            await self._send_command(21)

    async def check(self):
        if await self._check_auth():
            await self._send_command(255)
            data = await self._get_updates()
            await self._set_params(data)

    async def _set_params(self, data: dict):
        if not self._device_id:
            logger.warning("Device ID не установлен, невозможно обновить параметры")
            return

        stats = data.get("stats", {})
        device_stats = stats.get(str(self._device_id), {})

        # Берём нужные параметры
        self.engine_temp = device_stats.get("engine_temp")
        self.out_temp = device_stats.get("out_temp")
        self.voltage = device_stats.get("voltage")

        logger.debug(
            "Обновлены параметры: engine_temp=%s, out_temp=%s, voltage=%s",
            self.engine_temp,
            self.out_temp,
            self.voltage,
        )


# Пример использования
async def _test():
    async with Pandora() as pandora:
        await pandora.check()


if __name__ == "__main__":
    asyncio.run(_test())
