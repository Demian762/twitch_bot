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
Version: 250927 (Refactor completo)
Repository: https://github.com/Demian762/twitch_bot
"""

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
    """
    Clase principal del BotDelEstadio que extiende twitchio.Bot
    
    Esta clase maneja toda la lógica principal del bot de Twitch, incluyendo
    la inicialización de componentes, manejo de eventos, y coordinación
    entre diferentes sistemas (APIs, Telegram, comandos, etc.).
    
    Attributes:
        config (BotConfig): Configuración del bot y listas de datos
        api (APIManager): Manejador de todas las APIs externas
        state (BotState): Estado interno del bot (grog, rutinas, etc.)
        lista_programacion (list): Programación semanal del stream
        rutina_lista (list): Lista de rutinas automáticas
        telegram_bot (TelegramVoiceBot): Bot integrado de Telegram
        my_cogs (dict): Diccionario de cogs/comandos cargados
    
    Example:
        >>> bot = Bot()
        >>> bot.run()
    """

    def __init__(self):
        """
        Inicializa el bot con todas sus dependencias y configuraciones
        
        Proceso de inicialización:
        1. Configurar cliente de Twitch con token y canales
        2. Inicializar configuraciones (BotConfig, APIManager, BotState)
        3. Configurar rutinas automáticas
        4. Reproducir sonido de bienvenida
        5. Inicializar bot de Telegram
        6. Cargar todos los cogs de comandos
        
        Raises:
            Exception: Si falla la inicialización de componentes críticos
        """
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
        """
        Evento que se ejecuta cuando el bot se conecta exitosamente a Twitch
        
        Se ejecuta una vez que el bot se autentica y está listo para recibir
        comandos y eventos. Inicia el bot de Telegram en paralelo.
        """
        logger.info(f'Logueado a Twitch como {self.nick}')
        asyncio.create_task(self._start_telegram_bot())

    async def _start_telegram_bot(self):
        """
        Inicia el bot de Telegram de forma asíncrona
        
        Este método se ejecuta en paralelo al bot de Twitch para proporcionar
        funcionalidades adicionales como conversión de audio y comandos específicos
        de Telegram. Los errores se capturan y registran sin afectar el bot principal.
        
        Raises:
            Exception: Captura y registra errores del bot de Telegram sin interrumpir
                      el funcionamiento del bot principal de Twitch
        """
        try:
            await self.telegram_bot.start_async()
        except Exception as e:
            logger.error(f"Error con bot de Telegram: {e}")

    async def event_error(self, error: Exception, data: str = None):
        """
        Manejador global de errores del bot
        
        Captura y registra todos los errores no manejados que ocurran en el bot,
        proporcionando información detallada para debugging.
        
        Args:
            error (Exception): La excepción que ocurrió
            data (str, optional): Datos adicionales sobre el contexto del error
        """
        logger.error(f"Error en el bot: {error}")
        if data:
            logger.error(f"Datos adicionales: {data}")

    async def event_command_error(self, ctx: commands.Context, error: Exception):
        """
        Manejador específico de errores de comandos
        
        Procesa errores que ocurren durante la ejecución de comandos,
        diferenciando entre comandos inexistentes y errores reales.
        
        Args:
            ctx (commands.Context): Contexto del comando que falló
            error (Exception): El error que ocurrió durante la ejecución
        
        Behavior:
            - CommandNotFound: Solo registra el intento sin mostrar error al usuario
            - Otros errores: Registra y notifica al chat con mensaje gracioso
        """
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
        """
        Determina si el bot está en coma etílico
        
        El bot entra en "coma etílico" después de consumir demasiado grog,
        lo que afecta su comportamiento en algunos comandos.
        
        Returns:
            str or False: Mensaje aleatorio de coma etílico si está borracho,
                         False si está sobrio
        
        Note:
            El estado de coma etílico se basa en el contador de grog consumido
            comparado con la longitud de la lista de mensajes de grog disponibles.
        """
        if self.state.grog_count >= len(grog_list):
            return choice(coma_etilico_list)
        return False

bot = Bot()
bot.run()
