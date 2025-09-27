from twitchio.ext import commands

# Imports locales
from utils.mensaje import mensaje
from utils.utiles_general import get_args
from utils.api_games import howlong, steam_price
from utils.logger import logger
from utils.configuracion import admins
from .base_command import BaseCommand

class GameCommands(BaseCommand):
    @commands.command()
    async def info(self, ctx: commands.Context, *args):
        if await self.check_coma_etilico():
            return
            
        handler = await self.handle_command(self._info)
        await handler(ctx, *args)

    async def _info(self, ctx: commands.Context, *args):
        juego = get_args(args)
        nombre, puntaje, fecha = self.bot.api.rawg.info(juego)
        if nombre == 200:
            await mensaje("La base de datos no está funcionando bien, intentá en un toque!")
            return
        if nombre is None:
            await mensaje("No se encontró nada en la base de datos!")
            return
        try:
            tiempo = howlong(juego)
        except:
            tiempo = None
        nombre_steam, precio = steam_price(nombre, self.bot.api.steam, self.bot.api.dolar)
        sep = " // "
        output = nombre
        if puntaje:
            output = output + sep + str(puntaje) + " puntos en Metacritic"
        if fecha:
            output = output + sep + fecha
        if tiempo:
            output = output + sep + tiempo + " horas"
        if nombre_steam:
            output = output + sep + str(precio) + " pesos en Steam."
        output = output + "."
        await mensaje(output)

    @commands.command()
    async def lanzamientos(self, ctx: commands.Context, limite = 3):
        if await self.check_coma_etilico():
            return
            
        handler = await self.handle_command(self._lanzamientos) 
        await handler(ctx, limite)

    async def _lanzamientos(self, ctx: commands.Context, limite):
        if ctx.author.name not in admins and limite > 3:
            limite = 3
        output = self.bot.api.rawg.lanzamientos(limite)
        if output is not False:
            await mensaje(output)
        else:
            await mensaje("No encontré lanzamientos.")
