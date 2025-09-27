from twitchio.ext import commands

# Imports locales
from utils.mensaje import mensaje
from utils.puntitos_manager import consulta_puntitos, consulta_historica
from .base_command import BaseCommand

class PointsCommands(BaseCommand):
    @commands.command(aliases=("puntos","punto","puntitos","score"))
    async def consulta(self, ctx: commands.Context):
        if await self.check_coma_etilico():
            return
            
        nombre = ctx.author.name
        puntitos = consulta_puntitos(nombre)
        if puntitos == 0:
            await ctx.send(f'@{nombre} todavía no tiene puntitos!')
        elif puntitos == 1 or puntitos == -1:
            await mensaje(f'@{nombre} tiene {puntitos} puntito!')
        else:
            await mensaje(f'@{nombre} tiene {puntitos} puntitos!')

    @commands.command(aliases=())
    async def historico(self, ctx: commands.Context):
        if await self.check_coma_etilico():
            return
            
        nombre = ctx.author.name
        puntitos = consulta_historica(nombre)
        if puntitos == 0:
            await ctx.send(f'@{nombre} todavía no tiene puntitos históricos!')
        elif puntitos == 1 or puntitos == -1:
            await mensaje(f'@{nombre} tiene {puntitos} puntito histórico!')
        else:
            await mensaje(f'@{nombre} tiene {puntitos} puntitos históricos!')
