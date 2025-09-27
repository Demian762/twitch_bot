from twitchio.ext import commands
from utils.logger import logger
from utils.mensaje import mensaje
from .base_command import BaseCommand
from utils.configuracion import lista_redes, lista_amigos, cafecito_texto

class InfoCommands(BaseCommand):
    @commands.command()
    async def redes(self, ctx: commands.Context):
        if await self.check_coma_etilico():
            return
        await mensaje(lista_redes)
    
    @commands.command()
    async def discord(self, ctx: commands.Context):
        if await self.check_coma_etilico():
            return
        await mensaje("¡Sumate a nuestro Discord! https://discord.gg/YDdPMDxFDd")
        
    @commands.command(aliases=("programación",))
    async def programacion(self, ctx: commands.Context):
        if await self.check_coma_etilico():
            return
        await mensaje(self.bot.lista_programacion)

    @commands.command(aliases=("amigo",))
    async def amigos(self, ctx: commands.Context):
        if await self.check_coma_etilico():
            return
        await mensaje(lista_amigos)

    @commands.command(aliases=("cafe",))
    async def cafecito(self, ctx: commands.Context):
        if await self.check_coma_etilico():
            return
        await mensaje(cafecito_texto)
