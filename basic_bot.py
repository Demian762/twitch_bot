import twitchio
from twitchio.ext import commands, routines
from twitch_secrets import (twitch_token, rawg_url, rawg_key)
from utiles import (imprimir_md, steam_api)
from rawgio import rawg
import random

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=twitch_token,
                         prefix='!',
                         initial_channels=['hablemosdepavadaspod']) # 'Demian762'
        try:
            self.rawg = rawg(rawg_url, rawg_key)
        except:
            print("Conexión con RAWG fallida.")
        try:
            self.steam = steam_api()
        except:
            print("No se pudo conectar a Steam.")

        self.instanciacion.start()

    async def event_ready(self):
        print(f'Logueado a Twitch como {self.nick}.')

    @routines.routine(seconds=1, iterations=1)
    async def instanciacion(self):
        if len(self.connected_channels) > 0:
            await self.connected_channels[0].send("Acaba de entrar en juego EL BOT DEL ESTADIO")
        
    @commands.command()
    async def hola(self, ctx: commands.Context):
        await ctx.send(f'Hola {ctx.author.name}!')

    @commands.command()
    async def medimela(self, ctx: commands.Context):
        hdp = ["demian762",self.nick]
        if ctx.author.name in hdp:
            largo = 25
        else:
            largo = int(random.uniform(1, 24))
        await ctx.send(f'A {ctx.author.name} le mide {largo} centímetros')

    @commands.command()
    async def quiensos(self, ctx: commands.Context):
        await ctx.send(f'En realidad soy Sergio... me descubrieron.')
    
    @commands.command()
    async def redes(self, ctx: commands.Context):
        #texto = imprimir_md("./markdown/redes.md")
        #await ctx.send(texto)
        await ctx.send('Instagram https://www.instagram.com/hablemosdepavadas/')
        await ctx.send('YouTube https://www.youtube.com/@hablemosdepavadaspodcast')

    @commands.command()
    async def _botcolor(self, ctx: commands.Context, color: str):
        await ctx.send('/color ' + color)
        await ctx.send(f'{ctx.author.name} me cambió de color!')

    @commands.command()
    async def programacion(self, ctx: commands.Context):
        await ctx.send('MARTES de entre casa con Juan, noticias y jueguitos chill.')
        await ctx.send('MIÉRCOLES de PCMR con Demian, llevando al límite los FPS.')
        await ctx.send('VIERNES de Super Aventuras con Sergio y Juan, Aventuras gráficas con expertos en la materia.')
        await ctx.send('SÁBADOS de Contenido Retro con Ever, un viaje al pasado y la nostalgia.')

    @commands.command()
    async def cafecito(self, ctx: commands.Context):
        await ctx.send('Si les gusta nuestro contenido pueden ayudarnos con un cafecito a https://cafecito.app/hablemosdepavadas')

    @commands.command()
    async def info(self, ctx: commands.Context, *args):
        juego = ""
        for i in args:
            juego = juego + " " + i
        juego = juego.strip()
        nombre, puntaje = self.rawg.info(juego)

        if nombre is not None or nombre is not False:
            if puntaje is not None:
                await ctx.send(nombre + " tiene un puntaje de: " + str(puntaje) + " en Metacritic, según rawg.io.")
            else:
                await ctx.send(nombre + " todavía no tiene puntaje en Metacritic según rawg.io.")
            try:
                steam_data = self.steam.apps.search_games(nombre)['apps'][0]
                await ctx.send(steam_data['name'] + " tiene un precio en dólares de " + steam_data['price'] + " en Steam.")
            except:
                await ctx.send(f'No se encontró {nombre} en la base de datos de Steam.')
        else:
            await ctx.send(f'Escribí bien {ctx.author.name}!')



bot = Bot()
bot.run()
