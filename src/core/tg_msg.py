from apps.pandora.api import PandoraState
from core.config import bot, settings


async def _send_msg(text: str):
    await bot.send_message(
        text=text,
        chat_id=settings.telegram.admin_chat_id,
        parse_mode="MarkdownV2",
    )


async def msg_wait(state: PandoraState):
    text = f"🌡️ Прогрев: {state.engine_temp}°C (попытка {state.count}/10)"
    await _send_msg(text)


async def msg_params(state: PandoraState):
    text = (
        f"🌡️ **Начальные параметры:**\n"
        f"Двигатель: {state.engine_temp} °C\n"
        f"Улица: {state.out_temp} °C\n"
        f"Аккумулятор: {state.voltage} V"
    )
    await _send_msg(text)


async def msg_cold_start():
    text = (
        "❄️ **Холодный запуск:** Холодная погода и холодный двигатель.\n"
        "Начинаем прогрев до 30°C."
    )
    await _send_msg(text)


async def msg_start_wo_heater(state: PandoraState):
    text = (
        f"☀️ **Обычный запуск:**\n"
        f"(Улица: {state.out_temp}°C,\n"
        f"Двигатель: {state.engine_temp_before}°C).\n"
        f"Запуск двигателя, подогреватель не включился."
    )
    await _send_msg(text)


async def msg_ready(state: PandoraState):
    text = (
        f"✅ **Успех!** Двигатель прогрет до {state.engine_temp}°C.\n"
        f"Производится запуск двигателя."
    )
    await _send_msg(text)


async def msg_normal_start(state: PandoraState):
    text = (
        f"☀️ **Обычный запуск:**\n"
        f"Улица: {state.out_temp}°C\n"
        f"Двигатель: {state.engine_temp_before}°C.\n"
        f"Запуск двигателя без предварительного прогрева."
    )
    await _send_msg(text)
