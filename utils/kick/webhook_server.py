"""
Servidor de webhooks de eventos de Kick.

Kick empuja eventos (chat.message.sent, follows, subs, etc.) a una URL HTTPS
pública, configurada una sola vez en el panel de developer de la app (no se
manda por API — ver utils/kick/client.py:subscribe_events). Este módulo
levanta el servidor LOCAL que debe quedar detrás de esa URL pública — hace
falta un túnel (Cloudflare Tunnel, ngrok, etc.) o un reverse proxy que
apunte acá, ya que el bot corre en la PC del usuario sin IP pública fija.

Cada request se valida con la firma RSA-SHA256 que manda Kick antes de
procesarla, para no ejecutar comandos a partir de webhooks falsificados.

Referencia: https://github.com/KickEngineering/KickDevDocs/blob/main/events/webhook-security.md
"""

import base64
from collections.abc import Awaitable, Callable

from aiohttp import web
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

from utils.logger import logger

EventCallback = Callable[[str, dict], Awaitable[None]]


class KickWebhookServer:
    def __init__(self, host: str, port: int, public_key_pem: str, on_event: EventCallback) -> None:
        self.host = host
        self.port = port
        self._on_event = on_event
        self._public_key: RSAPublicKey = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        self._runner: web.AppRunner | None = None

    def _verify_signature(self, message_id: str, timestamp: str, raw_body: bytes, signature_b64: str) -> bool:
        try:
            signed_payload = f"{message_id}.{timestamp}.".encode("utf-8") + raw_body
            signature = base64.b64decode(signature_b64)
            self._public_key.verify(signature, signed_payload, padding.PKCS1v15(), hashes.SHA256())
            return True
        except (InvalidSignature, ValueError) as e:
            logger.warning(f"[kick_webhook] Firma inválida, request descartado: {e}")
            return False

    async def _handle(self, request: web.Request) -> web.Response:
        message_id = request.headers.get("Kick-Event-Message-Id", "")
        timestamp = request.headers.get("Kick-Event-Message-Timestamp", "")
        signature = request.headers.get("Kick-Event-Signature", "")
        event_type = request.headers.get("Kick-Event-Type", "")

        if not (message_id and timestamp and signature and event_type):
            return web.Response(status=400, text="Faltan headers de Kick")

        raw_body = await request.read()

        if not self._verify_signature(message_id, timestamp, raw_body, signature):
            return web.Response(status=401, text="Firma inválida")

        logger.debug(f"[kick_webhook] Evento recibido: {event_type} (message_id={message_id})")

        try:
            payload = await request.json()
        except Exception:
            return web.Response(status=400, text="Body inválido")

        try:
            await self._on_event(event_type, payload)
        except Exception as e:
            logger.error(f"[kick_webhook] Error procesando evento '{event_type}': {e}", exc_info=e)

        return web.Response(status=200, text="ok")

    async def start(self) -> None:
        app = web.Application()
        app.router.add_post("/kick/webhook", self._handle)
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, self.host, self.port, reuse_address=True)
        await site.start()
        logger.info(f"[kick_webhook] Escuchando en http://{self.host}:{self.port}/kick/webhook")

    async def stop(self) -> None:
        if self._runner:
            await self._runner.cleanup()
            logger.info("[kick_webhook] Servidor detenido")
