import twitchio
from twitchio.ext import commands, routines
from twitch_secrets import (twitch_token, rawg_url, rawg_key)
from utiles import imprimir_md
from rawgio import rawg
import random

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=twitch_token,
                         prefix='!',
                         initial_channels=['hablemosdepavadaspod']) # 'Demian762'
        try:
            self.rawg = rawg(rawg_url, rawg_key)
            self.rawg_con = True
        except:
            print("NO conectado a RAWG.")
            self.rawg_con = False
        self.instanciacion.start()

    async def event_ready(self):
        print(f'Logueado a Twitch como {self.nick}.')

    @routines.routine(seconds=1, iterations=1)
    async def instanciacion(self):
        if len(self.connected_channels) > 0:
            await self.connected_channels[0].send("Acaba de entrar en juego EL BOT DEL ESTADIO")
        
    @commands.command()
    async def hello(self, ctx: commands.Context):
        await ctx.send(f'Hello {ctx.author.name}!')

    @commands.command()
    async def largo(self, ctx: commands.Context):
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
        texto = imprimir_md("./markdown/redes.md")
        #await ctx.send(texto)
        await ctx.send('Instagram https://www.instagram.com/hablemosdepavadas/')
        await ctx.send('YouTube https://www.youtube.com/@hablemosdepavadaspodcast')

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
        if not self.rawg_con:
            return await ctx.send(f'Perdón {ctx.author.name}, La base de datos está offline!')
        juego = ""
        for i in args:
            juego = juego + " " + i
        juego = juego.strip()
        nombre, puntaje = self.rawg.info(juego)

        if nombre:
            await ctx.send("Nombre completo del juego: " + nombre)
            await ctx.send("Metacritic: " + str(puntaje))
        else:
            await ctx.send(f'Escribí bien {ctx.author.name}!')

bot = Bot()
bot.run()
