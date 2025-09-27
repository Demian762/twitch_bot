"""
Comandos informativos del canal y comunidad

Este módulo proporciona comandos para mostrar información sobre redes sociales,
Discord, programación, amigos del canal y donaciones.

Author: Demian762
Version: 250927
"""

from twitchio.ext import commands
from utils.logger import logger
from utils.mensaje import mensaje
from .base_command import BaseCommand
from utils.configuracion import lista_redes, lista_amigos, cafecito_texto

class InfoCommands(BaseCommand):
    """
    Cog para comandos informativos del canal
    
    Proporciona información sobre redes sociales, Discord, programación,
    amigos del canal y métodos de donación.
    
    Attributes:
        bot: Instancia del bot principal
        lista_redes: Texto con enlaces a redes sociales
        lista_amigos: Lista de canales amigos
        cafecito_texto: Información sobre donaciones
    """
    @commands.command()
    async def redes(self, ctx: commands.Context):
        """
        Muestra las redes sociales del canal
        
        Args:
            ctx: Contexto del comando de Twitch
        """
        if await self.check_coma_etilico():
            return
        await mensaje(lista_redes)
    
    @commands.command()
    async def discord(self, ctx: commands.Context):
        """
        Muestra el enlace del servidor Discord
        
        Args:
            ctx: Contexto del comando de Twitch
        """
        if await self.check_coma_etilico():
            return
        await mensaje("¡Sumate a nuestro Discord! https://discord.gg/YDdPMDxFDd")
        
    @commands.command(aliases=("programación",))
    async def programacion(self, ctx: commands.Context):
        """
        Muestra la programación actual del canal
        
        Args:
            ctx: Contexto del comando de Twitch
        """
        if await self.check_coma_etilico():
            return
        await mensaje(self.bot.lista_programacion)

    @commands.command(aliases=("amigo",))
    async def amigos(self, ctx: commands.Context):
        """
        Muestra la lista de canales amigos
        
        Args:
            ctx: Contexto del comando de Twitch
        """
        if await self.check_coma_etilico():
            return
        await mensaje(lista_amigos)

    @commands.command(aliases=("cafe",))
    async def cafecito(self, ctx: commands.Context):
        """
        Muestra información sobre donaciones
        
        Args:
            ctx: Contexto del comando de Twitch
        """
        if await self.check_coma_etilico():
            return
        await mensaje(cafecito_texto)
