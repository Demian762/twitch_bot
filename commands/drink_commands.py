from twitchio.ext import commands
from utils.mensaje import mensaje
from utils.configuracion import grog_list
from .base_command import BaseCommand

class DrinkCommands(BaseCommand):
    @commands.command()
    async def grog(self, ctx: commands.Context):
        if await self.check_coma_etilico():
            return
        
        # Verificar si el contador no excede la lista
        if self.bot.state.grog_count >= len(grog_list):
            self.bot.state.grog_count = len(grog_list) - 1
            
        texto = grog_list[self.bot.state.grog_count]
        await mensaje(texto)
        self.bot.state.grog_count += 1
    
    @commands.command(aliases=("agüita","aguita"))
    async def agua(self, ctx: commands.Context):
        self.bot.state.grog_count = 0
        await mensaje(f'Gracias {ctx.author.name} por darle agua al Bot.')
