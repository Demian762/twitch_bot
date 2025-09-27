# Imports estándar
import asyncio
import winsound
from random import choice

# Imports de terceros
from twitchio.ext import commands
from twitchio.ext.commands.errors import CommandNotFound

# Imports locales - utiles
from utils.logger import logger
from utils.mensaje import mensaje, sendMessage, openSocket
from utils.utiles_general import resource_path
from utils.bot_config import BotConfig, APIManager, BotState
from utils.secretos import (
    access_token, 
    rawg_url, 
    rawg_key, 
    telegram_bot_token
)

# Imports locales - otros
from telegram_bot.telegram_voice_bot import TelegramVoiceBot
from utils.configuracion import (
    grog_list,
    coma_etilico_list
)
from commands import COGS


class Bot(commands.Bot):

    def __init__(self):
        try:
            super().__init__(token=access_token,
                            prefix='!',
                            initial_channels=['hablemosdepavadaspod', 'Demian762'],
                            case_insensitive = True)
            
            # Inicializar configuraciones y estados con manejo de errores
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
            
            # Asignar listas del config al bot para comandos
            self.lista_programacion = getattr(self.config, 'lista_programacion', [])
            
            # Configurar rutinas con validación
            self.rutina_lista = getattr(self.config, 'rutina_lista', [])
            if hasattr(self.api, 'ultimo_video'):
                self.rutina_lista.extend([self.api.ultimo_video, self.api.ultimo_podcast])
            self.state.rutinas_counter["total"] = len(self.rutina_lista) - 1
            
            # Inicializar Telegram y sonido
            audio_path = resource_path("storage\holis.wav")
            winsound.PlaySound(audio_path, winsound.SND_FILENAME)
            self.telegram_bot = TelegramVoiceBot(telegram_bot_token)
            sendMessage(openSocket(), "Hace su entrada, EL BOT DEL ESTADIO!")
            
            # Inicializar y cargar cogs
            self.my_cogs = {cog.__name__: cog(self) for cog in COGS}
            for cog in self.my_cogs.values():
                self.add_cog(cog)
            
            logger.info("Bot inicializado correctamente")
        except Exception as e:
            logger.error(f"Error crítico al inicializar el bot: {e}")
            raise

    async def event_ready(self):
        logger.info(f'Logueado a Twitch como {self.nick}')
        asyncio.create_task(self._start_telegram_bot())

    async def _start_telegram_bot(self):
        """Inicia el bot de Telegram de forma asíncrona"""
        try:
            await self.telegram_bot.start_async()
        except Exception as e:
            logger.error(f"Error con bot de Telegram: {e}")

    async def event_error(self, error: Exception, data: str = None):
        logger.error(f"Error en el bot: {error}")
        if data:
            logger.error(f"Datos adicionales: {data}")

    async def event_command_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, CommandNotFound):
            # Extraer el comando del mensaje
            comando_texto = ctx.message.content.strip()
            if comando_texto.startswith('!'):
                comando = comando_texto.split()[0][1:]  # Remover el ! y obtener solo el comando
                logger.info(f"El comando '{comando}' no existe - Usuario: {ctx.author.name}")
            return
        
        logger.error(f"Error en comando {ctx.command.name}: {error}")
        await mensaje("Ya rompiste el bot con ese comando...")

    def coma_etilico(self):
        if self.state.grog_count >= len(grog_list):
            return choice(coma_etilico_list)
        return False

bot = Bot()
bot.run()
