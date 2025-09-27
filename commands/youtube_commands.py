from twitchio.ext import commands
from utils.logger import logger
from utils.mensaje import mensaje
from utils.api_youtube import *
from .base_command import BaseCommand

class YoutubeCommands(BaseCommand):
    @commands.command()
    async def recomendame(self, ctx: commands.Context):
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
        if await self.check_coma_etilico():
            return
            
        video_id = get_latest_video(self.bot.yt_client)
        nombre_video, link_video = get_video_details(video_id, self.bot.yt_client)
        await mensaje([nombre_video, link_video])

    @commands.command()
    async def podcast(self, ctx: commands.Context):
        if await self.check_coma_etilico():
            return
            
        video_id = get_latest_podcast(self.bot.yt_client)
        nombre_video, link_video = get_video_details(video_id, self.bot.yt_client)
        await mensaje([nombre_video, link_video])
