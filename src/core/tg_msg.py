from apps.pandora.api import PandoraState
from core.config import bot, settings


async def _send_msg(text: str):
    await bot.send_message(
        text=text,
        chat_id=settings.telegram.admin_chat_id,
        parse_mode="HTML",
    )


async def msg_wait(state: PandoraState):
    """Сообщение о текущем прогреве."""
    text = f"🌡️ Прогрев: {state.engine_temp}°C (попытка {state.count}/15)"
    await _send_msg(text)


async def msg_params(state: PandoraState):
    """Сообщение о начальных параметрах."""
    text = (
        f"<b>🌡️ Начальные параметры:</b>\n"
        f"Двигатель: {state.engine_temp} °C\n"
        f"Улица: {state.out_temp} °C\n"
        f"Аккумулятор: {state.voltage} V"
    )
    await _send_msg(text)


async def msg_cold_start():
    """Сообщение о начале холодного запуска."""
    text = (
        f"❄️ <b>Холодный запуск:</b>\n"
        f"Холодная погода и холодный двигатель\n"
        f"Начинаем прогрев до 30°C"
    )
    await _send_msg(text)


async def msg_start_wo_heater(state: PandoraState):
    """Сообщение о запуске без подогревателя (если не удалось включить)."""
    text = (
        f"☀️ <b>Обычный запуск:</b>\n"
        f"Улица: {state.out_temp}°C\n"
        f"Двигатель: {state.engine_temp_before}°C\n"
        f"Запуск двигателя, подогреватель не включился."
    )
    await _send_msg(text)


async def msg_ready(state: PandoraState):
    """Сообщение об успешном прогреве и начале запуска."""
    text = (
        f"✅ <b>Успех!</b>\n"
        f"Двигатель прогрет до {state.engine_temp}°C\n"
        f"Производится запуск двигателя."
    )
    await _send_msg(text)


async def msg_normal_start(state: PandoraState):
    """Сообщение об обычном запуске без прогрева (условия не выполнены)."""
    text = (
        f"☀️ <b>Обычный запуск:</b>\n"
        f"Улица: {state.out_temp}°C\n"
        f"Двигатель: {state.engine_temp_before}°C\n"
        f"Запуск двигателя без предварительного прогрева"
    )
    await _send_msg(text)
