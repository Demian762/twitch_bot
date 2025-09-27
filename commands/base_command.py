"""
Clase base para todos los comandos del BotDelEstadio

Este módulo define la clase BaseCommand que proporciona funcionalidades
compartidas por todos los cogs de comandos del bot.

Author: Demian762
Version: 250927
"""

from twitchio.ext import commands

# Imports locales
from utils.logger import logger
from utils.mensaje import mensaje

class BaseCommand(commands.Cog):
    """
    Clase base abstracta para todos los comandos del bot
    
    Proporciona funcionalidades comunes como verificación de estado de embriaguez,
    manejo de errores y acceso a utilidades compartidas.
    
    Attributes:
        bot: Instancia del bot principal
        logger: Logger para registro de eventos y errores
    
    Methods:
        check_coma_etilico(): Verifica si el bot está en estado de embriaguez
        handle_command(): Decorador para manejo de errores en comandos
    """
    
    def __init__(self, bot):
        """
        Inicializa la clase base con referencia al bot principal
        
        Args:
            bot: Instancia del bot de Twitch principal
        """
        self.bot = bot
        self.logger = logger
        
    async def check_coma_etilico(self):
        """
        Verifica si el bot está en coma etílico y responde apropiadamente
        
        El bot puede entrar en "coma etílico" después de consumir demasiado grog,
        lo que temporalmente afecta su capacidad de responder a ciertos comandos.
        
        Returns:
            bool: True si el bot está en coma etílico y envió un mensaje,
                  False si está sobrio y puede responder normalmente
        
        Note:
            Cuando el bot está en coma etílico, responde con mensajes aleatorios
            de la lista coma_etilico_list y algunos comandos pueden no ejecutarse.
        """
        pedo = self.bot.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return True
        return False
        
    async def handle_command(self, func):
        """
        Decorador para manejo centralizado de errores en comandos
        
        Envuelve funciones de comando para capturar excepciones y proporcionar
        mensajes de error consistentes a los usuarios.
        
        Args:
            func: Función de comando a envolver
            
        Returns:
            function: Función wrapper con manejo de errores
            
        Example:
            @handle_command
            async def mi_comando(self, ctx):
                # código del comando
                pass
        """
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error en {func.__name__}: {e}")
                await mensaje("Ya rompiste el bot con ese comando...")
        return wrapper
