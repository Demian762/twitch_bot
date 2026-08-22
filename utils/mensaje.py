"""
Sistema de mensajería para comunicación con el chat (Twitch o Kick)

Expone una única función mensaje() usada por todos los comandos, sin importar
la plataforma activa. Quien arranca el bot registra el "sender" correspondiente
una vez al inicio:
  - Twitch: set_broadcaster(broadcaster, bot_id) — usa la API de twitchio V3.
  - Kick:   set_kick_sender(client, broadcaster_user_id) — usa utils/kick/client.py.

Solo una plataforma corre por proceso, así que nunca hay ambigüedad sobre
cuál de los dos senders está activo.

Author: Demian762
Version: 260810 (soporte multi-plataforma Twitch/Kick)
"""

import asyncio

from utils.configuracion import configuracion_basica

# Referencia al broadcaster de Twitch, guardada en setup_hook del bot de Twitch
_broadcaster = None
_bot_id: str | None = None

# Cliente REST de Kick y user_id del canal, guardados al arrancar el bot de Kick
_kick_client = None
_kick_broadcaster_user_id: int | None = None


def set_broadcaster(broadcaster, bot_id: str) -> None:
    """Guarda la referencia al broadcaster de Twitch y bot_id para uso en mensaje()."""
    global _broadcaster, _bot_id
    _broadcaster = broadcaster
    _bot_id = bot_id


def set_kick_sender(client, broadcaster_user_id: int) -> None:
    """Guarda el cliente REST de Kick y el user_id del canal para uso en mensaje()."""
    global _kick_client, _kick_broadcaster_user_id
    _kick_client = client
    _kick_broadcaster_user_id = broadcaster_user_id


def es_kick() -> bool:
    """True si la plataforma activa del proceso es Kick (vs. Twitch)."""
    return _kick_client is not None


async def _send_one(texto: str) -> None:
    if _broadcaster is not None:
        await _broadcaster.send_message(message=texto, sender=_bot_id)
    elif _kick_client is not None:
        await _kick_client.send_chat_message(_kick_broadcaster_user_id, texto)


async def mensaje(input) -> None:
    """
    Envía uno o varios mensajes al chat del canal, en la plataforma activa.

    Args:
        input (str | list | None): Mensaje individual, lista de mensajes, o None.
                                   Si es None, no hace nada.

    Note:
        Requiere que set_broadcaster() o set_kick_sender() haya sido llamado
        antes (en el setup del bot correspondiente).
        Para listas aplica delay anti-spam entre mensajes.
    """
    if input is None or (_broadcaster is None and _kick_client is None):
        return

    if isinstance(input, str):
        await _send_one(input)
        return

    for texto in input:
        await _send_one(texto)
        await asyncio.sleep(configuracion_basica.get("dont_spam"))
