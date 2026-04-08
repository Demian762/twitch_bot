"""
Sistema de mensajería para comunicación con el chat de Twitch

Utiliza la referencia al broadcaster (PartialUser) guardada en setup_hook
para enviar mensajes via la API de twitchio V3 (EventSub/HTTP).

Author: Demian762
Version: 260407 (migración twitchio V3)
"""

import asyncio

from utils.configuracion import configuracion_basica

# Referencia al broadcaster obtenida en setup_hook del bot
_broadcaster = None
_bot_id: str | None = None


def set_broadcaster(broadcaster, bot_id: str) -> None:
    """Guarda la referencia al broadcaster y bot_id para uso en mensaje()."""
    global _broadcaster, _bot_id
    _broadcaster = broadcaster
    _bot_id = bot_id


async def mensaje(input) -> None:
    """
    Envía uno o varios mensajes al chat del canal.

    Args:
        input (str | list | None): Mensaje individual, lista de mensajes, o None.
                                   Si es None, no hace nada.

    Note:
        Requiere que set_broadcaster() haya sido llamado antes (en setup_hook).
        Para listas aplica delay anti-spam entre mensajes.
    """
    if input is None or _broadcaster is None:
        return

    if isinstance(input, str):
        await _broadcaster.send_message(message=input, sender=_bot_id)
        return

    for texto in input:
        await _broadcaster.send_message(message=texto, sender=_bot_id)
        await asyncio.sleep(configuracion_basica.get("dont_spam"))
