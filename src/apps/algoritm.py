import asyncio
import logging
from typing import Optional

from apps.pandora.api import Pandora
import core.tg_msg as tg_msg
from core import settings
from core.config import bot

logger = logging.getLogger(__name__)


class ColdStart:
    def __init__(self, test: bool = False):
        self.pandora: Optional[Pandora] = None
        self.heater_on = False
        self.__test = test
        self.heater_retries = 2

    # ---------------------------
    # Основной сценарий
    # ---------------------------
    async def begin(self):
        logger.info("Начало процедуры холодного запуска")
        async with Pandora() as pandora:
            self.pandora = pandora
            await self._initialize_state()

            if self.pandora.state.engine_on:
                await self._notify("Двигатель уже запущен")
                return

            if self._is_cold_start_condition():
                await self._handle_cold_start()
            else:
                await self._handle_warm_start()

    # ---------------------------
    # Инициализация состояния
    # ---------------------------
    async def _initialize_state(self):
        await self.pandora.check()
        self.pandora.state.engine_temp_before = self.pandora.state.engine_temp
        self.pandora.state.voltage_before = self.pandora.state.voltage

        self._log_state()
        await tg_msg.msg_params(self.pandora.state)

    # ---------------------------
    # Проверка условий
    # ---------------------------
    def _is_cold_start_condition(self) -> bool:
        condition = (
            self.pandora.state.out_temp <= 5,
            self.pandora.state.engine_temp_before < 30,
        )
        return all(condition)

    # ---------------------------
    # Холодный запуск
    # ---------------------------
    async def _handle_cold_start(self):
        logger.info("Холодная погода и холодный двигатель — начинаем прогрев")
        await tg_msg.msg_cold_start()

        success = await self._try_start_heater()
        if not success:
            await self._start_without_heater()
            return

        await self._wait_for_warmup()

    # ---------------------------
    # Тёплый запуск
    # ---------------------------
    async def _handle_warm_start(self):
        logger.info("Условия тёплого запуска — запуск двигателя без прогрева")
        await tg_msg.msg_normal_start(self.pandora.state)
        await self._safe_start_engine()

    # ---------------------------
    # Попытка включить подогреватель
    # ---------------------------
    async def _try_start_heater(self) -> bool:
        self.pandora.state.count = 0
        for attempt in range(1, self.heater_retries + 1):
            logger.info(
                f"Попытка включения подогревателя ({attempt}/{self.heater_retries})"
            )
            await self._start_heater()
            if self.heater_on:
                return True
        logger.warning("Не удалось включить подогреватель")
        return False

    # ---------------------------
    # Запуск двигателя без подогревателя
    # ---------------------------
    async def _start_without_heater(self):
        await tg_msg.msg_start_wo_heater(self.pandora.state)
        await self._safe_start_engine()

    # ---------------------------
    # Ожидание прогрева
    # ---------------------------
    async def _wait_for_warmup(self):
        self.pandora.state.count = 0
        start_temp = self.pandora.state.engine_temp

        while self.pandora.state.engine_temp < 20 and self.pandora.state.count < 15:
            self.pandora.state.count += 1

            # Проверяем, не запущен ли двигатель вручную
            if self.pandora.state.engine_on:
                await self._notify(
                    "✅ Двигатель уже запущен, прекращаю ожидание прогрева"
                )
                return
            # Проверка через 5 циклов
            if self.pandora.state.count == 5:
                await self._second_check_heater(start_temp)

            await self._log_wait_state()
            await asyncio.sleep(120)
            await self.pandora.check()

        if self.pandora.state.engine_temp >= 20:
            await self._ready_to_start()
        else:
            await self._notify(
                "Не удалось достичь безопасной температуры для запуска двигателя"
            )

    # ---------------------------
    # Повторная проверка подогревателя
    # ---------------------------
    async def _second_check_heater(self, start_temp: float):
        if self.pandora.state.engine_temp < start_temp + 5:
            logger.warning(
                "Температура не выросла на 5°C за 5 циклов — повторно включаем подогреватель"
            )
            await self._notify(
                "⚠️ Температура не растёт — пробуем снова включить подогреватель"
            )

            await self._start_heater()
            if not self.heater_on:
                await self._notify(
                    "🚗 Подогреватель не включился — выполняем запуск двигателя"
                )
                await self._safe_start_engine()

    # ---------------------------
    # Хелперы для подогревателя
    # ---------------------------
    async def _start_heater(self) -> bool:
        logger.info("Включаем подогреватель двигателя")
        if not self.__test:
            await self.pandora.start_heater()
        await asyncio.sleep(180)
        return await self._check_heater()

    async def _check_heater(self) -> bool:
        self.heater_on = False
        await self.pandora.check()
        delta_v = self.pandora.state.voltage_before - self.pandora.state.voltage
        if delta_v >= 0.2:
            self.heater_on = True
            logger.info("Подогреватель работает корректно")
        else:
            logger.warning("Подогреватель не включился")
        return self.heater_on

    # ---------------------------
    # Завершение прогрева
    # ---------------------------
    async def _ready_to_start(self):
        logger.info("Двигатель достиг безопасной температуры — запускаем")
        await tg_msg.msg_ready(self.pandora.state)
        await self._safe_start_engine()

    # ---------------------------
    # Вспомогательные методы
    # ---------------------------
    async def _safe_start_engine(self):
        if not self.__test:
            await self.pandora.start_engine()

    @staticmethod
    async def _notify(text: str):
        logger.info(text)
        await bot.send_message(chat_id=settings.telegram.admin_chat_id, text=text)

    def _log_state(self):
        s = self.pandora.state
        logger.info(f"Температура двигателя: {s.engine_temp_before}°C")
        logger.info(f"Наружная температура: {s.out_temp}°C")
        logger.info(f"Напряжение аккумулятора: {s.voltage_before}V")

    async def _log_wait_state(self):
        logger.info(
            f"Температура двигателя: {self.pandora.state.engine_temp}°C — ждём прогрева"
        )
        await tg_msg.msg_wait(self.pandora.state)


# Пример использования
async def _test():
    await ColdStart(test=True).begin()


if __name__ == "__main__":
    asyncio.run(_test())
