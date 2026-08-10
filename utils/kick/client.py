"""
Cliente REST de la API pública de Kick (api.kick.com/public/v1).

No cachea el access_token: lo pide (get_token) en cada llamada, para no
duplicar la lógica de expiración/refresh que ya vive en utils/kick/auth.py.

Referencia: https://github.com/KickEngineering/KickDevDocs
"""

from collections.abc import Awaitable, Callable
from typing import Any

import aiohttp

from utils.logger import logger

BASE_URL = "https://api.kick.com/public/v1"

TokenProvider = Callable[[], Awaitable[str]]


class KickClient:
    """Envuelve las llamadas REST de Kick que usa el bot."""

    def __init__(self, get_token: TokenProvider) -> None:
        self._get_token = get_token

    async def _headers(self) -> dict:
        token = await self._get_token()
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    @staticmethod
    def _unwrap(data: Any) -> Any:
        """La mayoría de las respuestas de Kick vienen envueltas en {"data": ...}."""
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        return data

    async def send_chat_message(self, broadcaster_user_id: int, content: str) -> dict:
        """Envía un mensaje al chat del canal, como bot."""
        payload = {
            "broadcaster_user_id": broadcaster_user_id,
            "content": content[:500],
            "type": "bot",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/chat", json=payload, headers=await self._headers()) as resp:
                body = await resp.text()
                if resp.status >= 400:
                    logger.error(f"[kick_client] Error enviando mensaje ({resp.status}): {body}")
                    resp.raise_for_status()
                return self._unwrap(await resp.json())

    async def delete_chat_message(self, message_id: str) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.delete(f"{BASE_URL}/chat/{message_id}", headers=await self._headers()) as resp:
                resp.raise_for_status()

    async def subscribe_events(self, broadcaster_user_id: int, events: list[dict]) -> dict:
        """Suscribe la app a los eventos indicados (webhook push).

        La URL del webhook NO se manda acá: se configura una sola vez en el
        panel de developer de Kick, en la config de la app.
        """
        payload = {
            "broadcaster_user_id": broadcaster_user_id,
            "events": events,
            "method": "webhook",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/events/subscriptions", json=payload, headers=await self._headers()
            ) as resp:
                body = await resp.text()
                if resp.status >= 400:
                    logger.error(f"[kick_client] Error suscribiendo eventos ({resp.status}): {body}")
                    resp.raise_for_status()
                return self._unwrap(await resp.json())

    async def get_my_user(self) -> dict:
        """Info del usuario autorizado (incluye el user_id numérico del canal)."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/users", headers=await self._headers()) as resp:
                resp.raise_for_status()
                users = self._unwrap(await resp.json())
                if isinstance(users, list):
                    if not users:
                        raise RuntimeError("Kick no devolvió información del usuario autorizado.")
                    return users[0]
                return users

    async def get_channel(self, broadcaster_user_id: int) -> dict | None:
        """Info del canal (incluye stream_title). None si no se pudo obtener."""
        params = {"broadcaster_user_id": broadcaster_user_id}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/channels", params=params, headers=await self._headers()) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    logger.warning(f"[kick_client] Error obteniendo canal ({resp.status}): {body}")
                    return None
                channels = self._unwrap(await resp.json())
                if isinstance(channels, list):
                    return channels[0] if channels else None
                return channels

    async def get_public_key(self) -> str:
        """Clave pública RSA (PEM) usada para verificar la firma de los webhooks."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/public-key") as resp:
                resp.raise_for_status()
                data = self._unwrap(await resp.json())
                key = data.get("public_key") if isinstance(data, dict) else None
                if not key:
                    raise RuntimeError(f"No se pudo extraer la public_key de la respuesta de Kick: {data!r}")
                return key
