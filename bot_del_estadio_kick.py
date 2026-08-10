"""
BotDelEstadio - Bot de Kick para Hablemos de Pavadas

Entrypoint equivalente a bot_del_estadio.py pero para la plataforma Kick.
Reutiliza tal cual la misma lógica de negocio (COGS de commands/, BotConfig/
APIManager/BotState, puntitos, audio, minijuegos, trivia, integraciones) —
lo único que cambia es el transporte: acá no hay una conexión persistente
tipo IRC, Kick empuja los mensajes de chat y demás eventos vía webhooks HTTP
a un servidor propio (ver utils/kick/webhook_server.py).

Requisitos antes de arrancar:
  1. Registrar la app en https://kick.com/settings/developer (requiere 2FA)
     y completar kick_client_id / kick_client_secret / kick_redirect_uri en
     utils/secretos.py.
  2. Correr una vez: bot-env\\Scripts\\python.exe -m utils.kick.authorize
  3. Configurar en el panel de developer de la app la URL pública del
     webhook (un túnel — Cloudflare Tunnel, ngrok, etc. — apuntando a
     http://<kick_config.webhook_host>:<kick_config.webhook_port>/kick/webhook).

Gaps conocidos frente a Twitch (ver utils/kick/):
  - No hay evento de "raid" en la API de Kick.
  - No hay overlay de emotes de Kick (el actual es específico de Twitch).
  - No se reimplementó el watchdog de reconexión (acá no aplica igual,
    porque el chat llega por webhook y no por una conexión persistente).

Author: Demian762
Version: 260810 (integración Kick)
"""

import asyncio
import os
import shutil
import sys
import time
from random import choice

from utils.logger import logger
from utils import mensaje as mensaje_module
from utils.calendario_celebraciones import get_mensaje_diade
from utils.utiles_general import resource_path, play_sound
from utils.bot_config import BotConfig, APIManager, BotState
from utils.configuracion import BUILD_DATE, kick_config, grog_list, coma_etilico_list
from utils.secretos import rawg_url, rawg_key, telegram_bot_token, discord_webhook_url
from utils.puntitos_manager import set_bot_state
from utils.discord_notifier import notificar_titulo
from utils.metrics_server import MetricsServer

from utils.kick.auth import get_access_token
from utils.kick.client import KickClient
from utils.kick.webhook_server import KickWebhookServer
from utils.kick.dispatcher import KickCommandDispatcher

from telegram_bot.telegram_voice_bot import TelegramVoiceBot


class _ChannelInfo:
    """Objeto mínimo con .title, para que fetch_channel() sea compatible con
    lo que esperan !titulo / !notificar en commands/info_commands.py."""

    def __init__(self, title: str) -> None:
        self.title = title


class KickBot:
    """
    Bot de Kick — expone la misma superficie que bot_del_estadio.Bot usa como
    `self.bot` dentro de commands/*.py (config, api, state, my_cogs, metrics,
    coma_etilico(), fetch_channel(), etc.) para que los Components corran sin
    ningún cambio, sea cual sea la plataforma.
    """

    def __init__(self):
        try:
            self.config = BotConfig()
        except Exception as e:
            logger.error(f"Error al inicializar BotConfig: {e}")
            raise

        try:
            self.api = APIManager(rawg_url, rawg_key)
        except Exception as e:
            logger.error(f"Error al inicializar APIManager: {e}")
            raise

        self.state = BotState()
        self.metrics = MetricsServer()
        self.metrics._bot_state = self.state
        set_bot_state(self.state)

        self.lista_programacion = getattr(self.config, "lista_programacion", [])
        self.videos = getattr(self.api, "videos", [])

        self.rutina_lista = getattr(self.config, "rutina_lista", [])
        if hasattr(self.api, "ultimo_video"):
            self.rutina_lista[-1] = self.api.ultimo_video
        self.state.rutinas_counter["total"] = len(self.rutina_lista) - 1

        audio_path = resource_path("storage/audios/holis.wav")
        play_sound(audio_path)
        self.telegram_bot = TelegramVoiceBot(telegram_bot_token)

        self.client = KickClient(get_access_token)
        self.dispatcher = KickCommandDispatcher(self)
        self.my_cogs = self.dispatcher.components

        self.broadcaster_id: int | None = None
        self.webhook_server: KickWebhookServer | None = None
        self._tunnel_process: asyncio.subprocess.Process | None = None
        self._last_chat_ts = time.monotonic()

        logger.info("KickBot inicializado correctamente")

    # ── Superficie compartida con bot_del_estadio.Bot (usada por commands/*.py) ──

    def coma_etilico(self):
        if self.state.grog_count >= len(grog_list):
            return choice(coma_etilico_list)
        return False

    def get_usuarios_activos(self):
        return self.state.usuarios_activos

    def limpiar_usuarios_activos(self):
        self.state.usuarios_activos.clear()
        logger.info("Registro de usuarios activos limpiado")

    async def fetch_channel(self, broadcaster_id):
        data = await self.client.get_channel(broadcaster_id)
        if not data:
            return None
        return _ChannelInfo(title=data.get("stream_title", ""))

    # Ubicaciones típicas donde winget instala cloudflared en Windows — fallback
    # por si el PATH del proceso todavía no tiene la entrada nueva (pasa si no
    # se reinició la sesión/Explorer desde que se instaló).
    _CLOUDFLARED_FALLBACK_PATHS = (
        r"C:\Program Files (x86)\cloudflared\cloudflared.exe",
        r"C:\Program Files\cloudflared\cloudflared.exe",
    )

    def _find_cloudflared(self) -> str | None:
        found = shutil.which("cloudflared")
        if found:
            return found
        for path in self._CLOUDFLARED_FALLBACK_PATHS:
            if os.path.exists(path):
                return path
        return None

    async def _start_tunnel(self) -> None:
        """Levanta cloudflared (tunnel ya creado con `cloudflared tunnel create`,
        con su ruta DNS y config.yml en ~/.cloudflared/) para que el webhook
        server sea alcanzable públicamente. Se instala una vez por máquina con:
        winget install --id Cloudflare.cloudflared
        """
        tunnel_name = kick_config.get("cloudflare_tunnel_name")
        if not tunnel_name:
            logger.info("[kick] cloudflare_tunnel_name no configurado — no se levanta ningún túnel")
            return
        cloudflared_bin = self._find_cloudflared()
        if not cloudflared_bin:
            logger.warning(
                "[kick] cloudflared no encontrado — el webhook no será alcanzable "
                "públicamente. Instalar con: winget install --id Cloudflare.cloudflared"
            )
            return
        try:
            self._tunnel_process = await asyncio.create_subprocess_exec(
                cloudflared_bin, "tunnel", "run", tunnel_name,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            logger.info(f"[kick] cloudflared iniciado (tunnel '{tunnel_name}', bin={cloudflared_bin})")
        except OSError as e:
            logger.warning(f"[kick] No se pudo iniciar cloudflared: {e}")
            self._tunnel_process = None

    async def _stop_tunnel(self) -> None:
        if not self._tunnel_process:
            return
        self._tunnel_process.terminate()
        try:
            await asyncio.wait_for(self._tunnel_process.wait(), timeout=5)
        except asyncio.TimeoutError:
            self._tunnel_process.kill()
        logger.info("[kick] cloudflared detenido")

    # ── Manejo de eventos entrantes ──────────────────────────────────────────

    async def _on_chat_message(self, username: str, text: str) -> None:
        self._last_chat_ts = time.monotonic()
        if text.startswith("!"):
            self.state.usuarios_activos.add(username)
        await self.dispatcher.dispatch(username, text)

    async def _on_webhook_event(self, event_type: str, payload: dict) -> None:
        if event_type == "chat.message.sent":
            sender = payload.get("sender") or {}
            # Kick reenvía por webhook también los mensajes del propio bot
            # (enviados con type="user" a nombre del canal) — filtrarlos,
            # igual que event_message hace con payload.chatter.id == self.bot_id
            # del lado de Twitch.
            if sender.get("user_id") == self.broadcaster_id:
                return
            username = (sender.get("username") or "").lower()
            content = payload.get("content", "")
            if username:
                await self._on_chat_message(username, content)
        elif event_type == "channel.followed":
            self.metrics.followers += 1
            logger.info(f"Nuevo follower (Kick) — Total: {self.metrics.followers}")
        elif event_type in ("channel.subscription.new", "channel.subscription.renewal"):
            self.metrics.subscribers += 1
            logger.info(f"Nuevo sub (Kick) — Total: {self.metrics.subscribers}")
        else:
            logger.info(f"[kick] Evento sin manejador específico: {event_type}")

    # ── Ciclo de vida ────────────────────────────────────────────────────────

    async def start(self) -> None:
        me = await self.client.get_my_user()
        self.broadcaster_id = me.get("user_id") or me.get("broadcaster_user_id")
        if not self.broadcaster_id:
            raise RuntimeError(f"No se pudo determinar el user_id del canal de Kick. Respuesta: {me!r}")
        username = me.get("username") or me.get("name") or "?"
        logger.info(f"Logueado a Kick como {username} (user_id={self.broadcaster_id})")

        mensaje_module.set_kick_sender(self.client, self.broadcaster_id)

        public_key = await self.client.get_public_key()
        self.webhook_server = KickWebhookServer(
            host=kick_config["webhook_host"],
            port=kick_config["webhook_port"],
            public_key_pem=public_key,
            on_event=self._on_webhook_event,
        )
        await self.webhook_server.start()
        await self._start_tunnel()

        await self.client.subscribe_events(self.broadcaster_id, kick_config["events"])
        logger.info(f"[kick] Suscripto a {len(kick_config['events'])} tipos de evento")

        logger.info(f"Versión del bot: {BUILD_DATE}")
        await mensaje_module.mensaje("Hace su entrada, EL BOT DEL ESTADIO!")
        if msg_diade := get_mensaje_diade(fallback=False):
            await mensaje_module.mensaje(msg_diade)

        asyncio.create_task(self._start_telegram_bot())
        asyncio.create_task(self._notificar_discord_si_en_vivo())

        try:
            claudio_cog = self.my_cogs.get("ClaudioCommands")
            if claudio_cog:
                self.state.claude_contexto = await asyncio.to_thread(claudio_cog.build_contexto_completo_sync)
                logger.info("Contexto de Claude cargado (programación + puntitos + comandos)")
        except Exception as e:
            logger.error(f"Error al cargar contexto de Claude: {e}")
            self.state.claude_contexto = ""

        logger.info("KickBot listo — esperando eventos por webhook")

    async def _start_telegram_bot(self) -> None:
        try:
            await self.telegram_bot.start_async()
        except Exception as e:
            logger.error(f"Error con bot de Telegram: {e}")

    async def _notificar_discord_si_en_vivo(self) -> None:
        try:
            channel = await self.fetch_channel(self.broadcaster_id)
            if channel and channel.title:
                await notificar_titulo(discord_webhook_url, channel.title)
        except Exception as e:
            logger.error(f"Error al notificar Discord al arrancar: {e}")

    async def close(self) -> None:
        await self.telegram_bot.stop_async()
        await self.metrics.stop()
        await self._stop_tunnel()
        if self.webhook_server:
            await self.webhook_server.stop()

    async def run_forever(self) -> None:
        metrics_flag = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".metrics_disabled")
        if os.path.exists(metrics_flag):
            logger.info("[metrics] Deshabilitado por flag — WebSocket no iniciado")
        else:
            try:
                await self.metrics.start()
            except OSError as e:
                logger.warning(f"[metrics] No se pudo iniciar el WebSocket: {e} — el bot continúa sin métricas")

        await self.start()
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass
        finally:
            await self.close()


async def _run() -> None:
    # KickBot() debe construirse DENTRO del event loop: instancia todos los
    # Components de COGS, y al menos uno de ellos (InteractionCommands, para
    # las rutinas periódicas) arranca un asyncio.Task en su __init__, lo que
    # requiere un loop corriendo (igual que en Twitch, donde eso pasa dentro
    # de setup_hook — ya con el loop de bot.run() activo).
    bot = KickBot()
    await bot.run_forever()


def main() -> None:
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        logger.info("KickBot detenido por el usuario")
        sys.exit(0)


if __name__ == "__main__":
    main()
