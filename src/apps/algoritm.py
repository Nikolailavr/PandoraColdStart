import asyncio
import logging
from typing import Optional

from apps.pandora.api import Pandora
import core.tg_msg as tg_msg

logger = logging.getLogger(__name__)


class ColdStart:
    def __init__(self):
        self.pandora: Optional[Pandora] = None
        self.heater_on = False
        self.__test = False

    async def begin(self):
        logger.info("Начало процедуры холодного запуска")
        # Используем контекстный менеджер для Pandora
        async with Pandora() as pandora:
            self.pandora = pandora
            await self.pandora.check()
            self.pandora.state.engine_temp_before = pandora.state.engine_temp
            self.pandora.state.voltage_before = pandora.state.voltage
            logger.info(
                f"Температура двигателя: {self.pandora.state.engine_temp_before}°C"
            )
            logger.info(f"Наружная температура: {self.pandora.state.out_temp}°C")
            logger.info(
                f"Напряжение аккумулятора: {self.pandora.state.voltage_before}V"
            )
            await tg_msg.msg_params(self.pandora.state)

            if (
                self.pandora.state.out_temp <= 5
                and self.pandora.state.engine_temp_before < 30
            ):
                logger.info("Холодная погода и холодный двигатель — начинаем прогрев")
                await tg_msg.msg_cold_start()

                # Включение подогревателя
                count = 0
                while count < 3 and not self.heater_on:
                    count += 1
                    logger.info(f"Попытка включения подогревателя ({count}/3)")
                    await self._start_heater()

                # Ожидание прогрева двигателя до 30°C
                if count == 3 or not self.heater_on:
                    await tg_msg.msg_start_wo_heater(self.pandora.state)
                    if not self.__test:
                        self.pandora.start_engine()
                else:
                    count = 0
                    while self.pandora.engine_temp < 30 and count < 10:
                        count += 1
                        await self.pandora.check()
                        logger.info(
                            f"Температура двигателя: {self.pandora.engine_temp}°C — ждём прогрева"
                        )
                        await tg_msg.msg_wait(self.pandora.state)
                        await asyncio.sleep(120)

                    # Проверка и запуск двигателя
                    if self.pandora.engine_temp >= 30:
                        logger.info(
                            "Двигатель достиг безопасной температуры — запускаем"
                        )
                        await tg_msg.msg_ready(self.pandora.state)
                        if not self.__test:
                            await self.pandora.start_engine()
                    else:
                        logger.warning(
                            "Не удалось достичь безопасной температуры для запуска двигателя"
                        )
            else:
                logger.info(
                    "Условия теплого запуска — запуск двигателя без прогрева"
                )
                await tg_msg.msg_normal_start(self.pandora.state)
                if not self.__test:
                    await self.pandora.start_engine()

    async def _start_heater(self) -> bool:
        logger.info("Включаем подогреватель двигателя")
        if not self.__test:
            await self.pandora.start_heater()
        await asyncio.sleep(180)
        return await self._check_heater()

    async def _check_heater(self) -> bool:
        self.heater_on = False
        await self.pandora.check()
        if self.pandora.state.voltage_before > self.pandora.state.voltage:
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
