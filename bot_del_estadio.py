"""
BotDelEstadio - Bot oficial de Twitch para Hablemos de Pavadas

Este módulo contiene la implementación principal del bot de Twitch que proporciona
entretenimiento interactivo para el stream de Hablemos de Pavadas.

Características principales:
    - Comandos interactivos de entretenimiento
    - Sistema de puntitos para viewers
    - Integración con APIs (RAWG, Steam, YouTube, DolarAPI)
    - Reproducción de audio y efectos sonoros
    - Bot de Telegram integrado para funciones adicionales
    - Sistema de trivia y minijuegos
    - Gestión de rutinas automáticas

Author: Demian762
Version: 260407 (migración twitchio V3)
Repository: https://github.com/Demian762/twitch_bot
"""

# Imports estándar
import asyncio
import os
import sys
from random import choice

# Imports de terceros
from twitchio import eventsub
from twitchio.ext import commands
from twitchio.ext.commands import CommandNotFound

# Imports locales - utiles
from utils.logger import logger
from utils import mensaje as mensaje_module
from utils.mensaje import mensaje
from utils.calendario_celebraciones import get_mensaje_diade
from utils.utiles_general import resource_path, play_sound
from utils.bot_config import BotConfig, APIManager, BotState
from utils.secretos import (
    rawg_url,
    rawg_key,
    telegram_bot_token,
    channel_name,
    twitch_app_id,
    twitch_app_secret,
    bot_id,
    broadcaster_access_token,
    broadcaster_refresh_token,
    bot_access_token,
    bot_refresh_token,
    discord_webhook_url,
)
from utils.configuracion import BUILD_DATE
from utils.puntitos_manager import funcion_puntitos, set_bot_state

CAMBIO_CAMBIO_REWARDS = {
    "09bc1126-f824-4240-99ad-8767f3358dac": 1,   # cambio cambio..        → 1 puntito
    "4aeab761-d5ae-4960-af54-8905634d015b": 10,  # cambio cambio cambio.. → 10 puntitos
}
from utils.discord_notifier import notificar_titulo
from utils.metrics_server import MetricsServer

# Imports locales - otros
from telegram_bot.telegram_voice_bot import TelegramVoiceBot
from utils.configuracion import (
    grog_list,
    coma_etilico_list
)
from commands import COGS


def _token_file_path() -> str:
    """Retorna la ruta del archivo de tokens junto al exe (o al script en desarrollo)."""
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, '.tio.tokens.json')


class Bot(commands.Bot):
    """
    Clase principal del BotDelEstadio que extiende twitchio.ext.commands.Bot (V3)

    Attributes:
        config (BotConfig): Configuración del bot y listas de datos
        api (APIManager): Manejador de todas las APIs externas
        state (BotState): Estado interno del bot (grog, rutinas, etc.)
        lista_programacion (list): Programación semanal del stream
        rutina_lista (list): Lista de rutinas automáticas
        telegram_bot (TelegramVoiceBot): Bot integrado de Telegram
        my_cogs (dict): Diccionario de components/comandos cargados
    """

    def __init__(self):
        super().__init__(
            client_id=twitch_app_id,
            client_secret=twitch_app_secret,
            bot_id=bot_id,
            prefix='!',
        )

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

        self.lista_programacion = getattr(self.config, 'lista_programacion', [])
        self.videos = getattr(self.api, 'videos', [])

        self.rutina_lista = getattr(self.config, 'rutina_lista', [])
        if hasattr(self.api, 'ultimo_video'):
            self.rutina_lista[-1] = self.api.ultimo_video
        self.state.rutinas_counter["total"] = len(self.rutina_lista) - 1

        audio_path = resource_path("storage/holis.wav")
        play_sound(audio_path)
        self.telegram_bot = TelegramVoiceBot(telegram_bot_token)

        logger.info("Bot inicializado correctamente")

    async def load_tokens(self, **_) -> None:
        """Carga tokens desde el directorio del exe/script, no desde el CWD."""
        await super().load_tokens(_token_file_path())

    async def save_tokens(self, **_) -> None:
        """Guarda tokens junto al exe/script, no en el CWD."""
        await super().save_tokens(_token_file_path())

    async def setup_hook(self) -> None:
        """
        Hook de inicialización asíncrona — se ejecuta antes de conectar al websocket.

        1. Obtiene el PartialUser del canal para envío de mensajes
        2. Suscribe al EventSub de chat del canal
        3. Carga todos los components (antes llamados cogs)
        """
        _metrics_flag = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".metrics_disabled")
        if os.path.exists(_metrics_flag):
            logger.info("[metrics] Deshabilitado por flag — WebSocket no iniciado")
        else:
            try:
                await self.metrics.start()
            except OSError as e:
                logger.warning(f"[metrics] No se pudo iniciar el WebSocket: {e} — el bot continúa sin métricas")

        # Obtener broadcaster para poder enviar mensajes desde mensaje()
        broadcaster_users = await self.fetch_users(logins=[channel_name])
        if not broadcaster_users:
            raise RuntimeError(f"No se encontró el canal: {channel_name}")
        broadcaster = broadcaster_users[0]
        broadcaster_partial = self.create_partialuser(user_id=broadcaster.id, user_login=broadcaster.name)

        # Registrar en el módulo mensaje para uso global
        mensaje_module.set_broadcaster(broadcaster_partial, self.bot_id)
        self.broadcaster_id = broadcaster.id

        # Los tokens de secretos.py siempre tienen prioridad sobre el cache
        if bot_access_token:
            await self.add_token(bot_access_token, bot_refresh_token)
        if broadcaster_access_token:
            await self.add_token(broadcaster_access_token, broadcaster_refresh_token)

        # Suscribir al chat del canal via EventSub WebSocket
        payload = eventsub.ChatMessageSubscription(
            broadcaster_user_id=broadcaster.id,
            user_id=self.bot_id,
        )
        await self.subscribe_websocket(payload=payload)

        # Suscribir a canjes de puntos del canal
        for reward_id in CAMBIO_CAMBIO_REWARDS:
            await self.subscribe_websocket(payload=eventsub.ChannelPointsRedeemAddSubscription(
                broadcaster_user_id=broadcaster.id,
                reward_id=reward_id,
            ))

        # Obtener conteos iniciales de followers y subscribers
        broadcaster_id_str = str(broadcaster.id)
        try:
            ch_followers = await self._http.get_channel_followers(
                broadcaster_id=broadcaster.id,
                token_for=broadcaster_id_str,
            )
            self.metrics.followers = ch_followers.total
            logger.info(f"Followers iniciales: {self.metrics.followers}")
        except Exception as e:
            logger.warning(f"No se pudo obtener followers iniciales: {e}")

        try:
            ch_subs = await self._http.get_broadcaster_subscriptions(
                token_for=broadcaster_id_str,
                broadcaster_id=broadcaster.id,
                first=1,
            )
            self.metrics.subscribers = ch_subs.total or 0
            logger.info(f"Subscribers iniciales: {self.metrics.subscribers}")
        except Exception as e:
            logger.warning(f"No se pudo obtener subscribers iniciales: {e}")

        # Suscribir a follows y subscribes vía EventSub
        # ChannelFollowSubscription requiere token del broadcaster (moderator_user_id debe coincidir con el token)
        try:
            await self.subscribe_websocket(
                payload=eventsub.ChannelFollowSubscription(
                    broadcaster_user_id=broadcaster.id,
                    moderator_user_id=broadcaster.id,
                ),
                as_bot=False,
                token_for=str(broadcaster.id),
            )
            logger.info("EventSub: suscripto a channel.follow")
        except Exception as e:
            logger.warning(f"EventSub channel.follow no disponible: {e}")

        try:
            await self.subscribe_websocket(payload=eventsub.ChannelSubscribeSubscription(
                broadcaster_user_id=broadcaster.id,
            ))
            logger.info("EventSub: suscripto a channel.subscribe")
        except Exception as e:
            logger.warning(f"EventSub channel.subscribe no disponible: {e}")

        try:
            await self.subscribe_websocket(payload=eventsub.ChannelSubscriptionEndSubscription(
                broadcaster_user_id=broadcaster.id,
            ))
            logger.info("EventSub: suscripto a channel.subscription.end")
        except Exception as e:
            logger.warning(f"EventSub channel.subscription.end no disponible: {e}")

        # Cargar components (equivalente a add_cog en V2)
        self.my_cogs = {}
        for cog_class in COGS:
            component = cog_class(self)
            await self.add_component(component)
            self.my_cogs[cog_class.__name__] = component

        # Cargar contexto completo para !claudio (después de los cogs para incluir lista de comandos)
        try:
            claudio_cog = self.my_cogs["ClaudioCommands"]
            self.state.claude_contexto = await asyncio.to_thread(
                claudio_cog.build_contexto_completo_sync
            )
            logger.info("Contexto de Claude cargado (programación + puntitos + comandos)")
        except Exception as e:
            logger.error(f"Error al cargar contexto de Claude: {e}")
            self.state.claude_contexto = ""

        logger.info(f"setup_hook completo — canal: {channel_name} (ID: {broadcaster.id})")

    async def event_ready(self) -> None:
        """Se ejecuta cuando el bot se conecta y está listo."""
        logger.info(f'Logueado a Twitch como {self.user}')
        logger.info(f'Versión del bot: {BUILD_DATE}')
        await mensaje("Hace su entrada, EL BOT DEL ESTADIO!")
        await mensaje(get_mensaje_diade())
        asyncio.create_task(self._start_telegram_bot())
        asyncio.create_task(self._notificar_discord_si_en_vivo())

    async def _notificar_discord_si_en_vivo(self):
        try:
            stream = None
            async for s in self.fetch_streams(user_ids=[self.broadcaster_id], max_results=1):
                stream = s
                break
            if not stream:
                return
            channel = await self.fetch_channel(self.broadcaster_id)
            if channel:
                await notificar_titulo(discord_webhook_url, channel.title)
        except Exception as e:
            logger.error(f"Error al notificar Discord al arrancar: {e}")

    async def event_message(self, payload) -> None:
        """
        Se ejecuta por cada mensaje del chat.

        En V3 el payload es twitchio.ChatMessage:
          - payload.chatter.id  → ID del usuario
          - payload.chatter.name → nombre del usuario
          - payload.text        → contenido del mensaje (antes .content)
        """
        # Ignorar mensajes del propio bot (V3 no tiene .echo)
        if payload.chatter.id == self.bot_id:
            return

        if payload.text.startswith('!'):
            username = payload.chatter.name.lower()
            self.state.usuarios_activos.add(username)

        await self.process_commands(payload)

    async def _start_telegram_bot(self):
        """Inicia el bot de Telegram de forma asíncrona."""
        try:
            await self.telegram_bot.start_async()
        except Exception as e:
            logger.error(f"Error con bot de Telegram: {e}")

    async def event_error(self, payload) -> None:
        """Manejador global de errores del bot."""
        logger.error(f"Error en el bot [{payload.listener.__name__}]: {payload.error}", exc_info=payload.error)

    async def event_command_error(self, payload) -> None:
        """
        Manejador de errores de comandos.

        En V3 recibe un CommandErrorPayload con:
          - payload.context   → el Context del comando
          - payload.exception → la excepción ocurrida
        """
        error = payload.exception
        ctx = payload.context

        if isinstance(error, CommandNotFound):
            comando_texto = ctx.message.text.strip() if ctx.message else ""
            if comando_texto.startswith('!'):
                comando = comando_texto.split()[0][1:]
                logger.info(f"El comando '{comando}' no existe — Usuario: {ctx.author.name}")
            return

        logger.error(f"Error en comando {ctx.command.name if ctx.command else '?'}: {error}")
        await mensaje("Ya rompiste el bot con ese comando...")

    async def event_custom_redemption_add(self, payload) -> None:
        puntitos = CAMBIO_CAMBIO_REWARDS.get(payload.reward.id)
        if puntitos is None:
            return
        username = payload.user.name
        await asyncio.to_thread(funcion_puntitos, username, puntitos)
        await mensaje(f"@{username} canjeó '{payload.reward.title}' y ganó {puntitos} puntito{'s' if puntitos > 1 else ''}!")
        logger.info(f"Redemption '{payload.reward.title}': +{puntitos} puntito(s) para {username}")

    async def event_follow(self, payload) -> None:
        self.metrics.followers += 1
        logger.info(f"Nuevo follower — Total: {self.metrics.followers}")

    async def event_subscription(self, payload) -> None:
        self.metrics.subscribers += 1
        logger.info(f"Nuevo sub — Total: {self.metrics.subscribers}")

    async def event_subscription_end(self, payload) -> None:
        self.metrics.subscribers = max(0, self.metrics.subscribers - 1)
        logger.info(f"Sub expirado — Total: {self.metrics.subscribers}")

    async def close(self) -> None:
        await self.metrics.stop()
        await super().close()

    def coma_etilico(self):
        """
        Determina si el bot está en coma etílico.

        Returns:
            str | False: Mensaje aleatorio de coma etílico, o False si está sobrio.
        """
        if self.state.grog_count >= len(grog_list):
            return choice(coma_etilico_list)
        return False

    def get_usuarios_activos(self):
        """Retorna el conjunto de usuarios que usaron comandos en esta sesión."""
        return self.state.usuarios_activos

    def limpiar_usuarios_activos(self):
        """Limpia el registro de usuarios activos."""
        self.state.usuarios_activos.clear()
        logger.info("Registro de usuarios activos limpiado")


bot = Bot()
bot.run()
