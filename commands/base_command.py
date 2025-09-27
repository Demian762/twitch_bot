from twitchio.ext import commands

# Imports locales
from utils.logger import logger
from utils.mensaje import mensaje

class BaseCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        
    async def check_coma_etilico(self):
        pedo = self.bot.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return True
        return False
        
    async def handle_command(self, func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error en {func.__name__}: {e}")
                await mensaje("Ya rompiste el bot con ese comando...")
        return wrapper
