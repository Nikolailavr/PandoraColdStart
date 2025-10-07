import asyncio
import logging
from typing import Optional

from apps.pandora.api import Pandora

logger = logging.getLogger(__name__)


class ColdStart:
    def __init__(self):
        self.pandora: Optional[Pandora] = None
        self.heater_on = False

    async def begin(self):
        logger.info("Начало процедуры холодного запуска")
        # Используем контекстный менеджер для Pandora
        async with Pandora() as pandora:
            self.pandora = pandora
            await self.pandora.check()
            self.pandora.engine_temp_before = self.pandora.engine_temp
            self.pandora.voltage_before = self.pandora.voltage
            logger.info(f"Температура двигателя: {self.pandora.engine_temp_before}°C")
            logger.info(f"Наружная температура: {self.pandora.out_temp}°C")
            logger.info(f"Напряжение аккумулятора: {self.pandora.voltage_before}V")

            if self.pandora.out_temp <= 5 and self.pandora.engine_temp_before < 30:
                logger.info("Холодная погода и холодный двигатель — начинаем прогрев")

                # Включение подогревателя
                count = 0
                while count < 5 and not self.heater_on:
                    count += 1
                    logger.info(f"Попытка включения подогревателя ({count}/5)")
                    await self._start_heater()

                # Ожидание прогрева двигателя до 30°C
                count = 0
                while self.pandora.engine_temp < 30 and count < 10:
                    count += 1
                    await self.pandora.check()
                    logger.info(
                        f"Температура двигателя: {self.pandora.engine_temp}°C — ждём прогрева"
                    )
                    await asyncio.sleep(60)

                # Проверка и запуск двигателя
                if self.pandora.engine_temp >= 30:
                    logger.info("Двигатель достиг безопасной температуры — запускаем")
                    await self.pandora.start_engine()
                else:
                    logger.warning(
                        "Не удалось достичь безопасной температуры для запуска двигателя"
                    )

            else:
                logger.info(
                    "Условия холодного запуска не выполнены — запуск двигателя без прогрева"
                )
                await self.pandora.start_engine()

    async def _start_heater(self) -> bool:
        logger.info("Включаем подогреватель двигателя")
        await self.pandora.heater_on()
        await asyncio.sleep(120)
        return await self._check_heater()

    async def _check_heater(self) -> bool:
        self.heater_on = False
        await self.pandora.check()
        if self.pandora.voltage_before > self.pandora.voltage:
            self.heater_on = True
            logger.info("Подогреватель работает корректно")
        else:
            logger.warning("Подогреватель не включился")
        return self.heater_on


# Пример использования
async def _test():
    await ColdStart().begin()


if __name__ == "__main__":
    asyncio.run(_test())
