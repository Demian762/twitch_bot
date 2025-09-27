"""
Comandos de integración con YouTube

Este módulo proporciona comandos para obtener recomendaciones de videos,
el último video publicado y el último podcast del canal.

Author: Demian762
Version: 250927
"""

from twitchio.ext import commands
from random import randint
from utils.logger import logger
from utils.mensaje import mensaje
from utils.api_youtube import *
from .base_command import BaseCommand

class YoutubeCommands(BaseCommand):
    """
    Cog para comandos de YouTube
    
    Maneja la interacción con la API de YouTube para obtener
    información de videos y podcasts del canal.
    
    Attributes:
        bot: Instancia del bot principal
        yt_client: Cliente de la API de YouTube
    """
    @commands.command()
    async def recomendame(self, ctx: commands.Context):
        """
        Proporciona una recomendación aleatoria de video del canal
        
        Selecciona aleatoriamente un video de la lista de videos disponibles
        y muestra su título con enlace.
        
        Args:
            ctx: Contexto del comando de Twitch
            
        Returns:
            None
        """
        if await self.check_coma_etilico():
            return
            
        if len(self.bot.videos) > 0:
            indice = randint(0, len(self.bot.videos) - 1)
            video_id = self.bot.videos.pop(indice)
            nombre_video, link_video = get_video_details(video_id, self.bot.yt_client)
            await mensaje([nombre_video, link_video])
        else:
            await mensaje("Me quedé sin recomendaciones por hoy...")

    @commands.command(aliases=("último", ))
    async def ultimo(self, ctx: commands.Context):
        """
        Muestra el último video publicado en el canal
        
        Obtiene el video más reciente del canal de YouTube
        y muestra su título con enlace.
        
        Args:
            ctx: Contexto del comando de Twitch
            
        Returns:
            None
        """
        if await self.check_coma_etilico():
            return
            
        video_id = get_latest_video(self.bot.yt_client)
        nombre_video, link_video = get_video_details(video_id, self.bot.yt_client)
        await mensaje([nombre_video, link_video])

    @commands.command()
    async def podcast(self, ctx: commands.Context):
        """
        Muestra el último podcast publicado
        
        Busca el podcast más reciente del canal y muestra
        su título con enlace.
        
        Args:
            ctx: Contexto del comando de Twitch
            
        Returns:
            None
        """
        if await self.check_coma_etilico():
            return
            
        video_id = get_latest_podcast(self.bot.yt_client)
        nombre_video, link_video = get_video_details(video_id, self.bot.yt_client)
        await mensaje([nombre_video, link_video])
