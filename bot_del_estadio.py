from twitchio.ext import commands, routines
from secretos import (access_token, rawg_url, rawg_key)
from utiles import (
    steam_api,steam_price,
    precio_dolar,
    build_yt_client,
    get_videos_list,
    get_video_details,
    get_latest_video,
    get_latest_podcast)
from rawgio import rawg
import pandas as pd
import random
import asyncio
from mensaje import openSocket, sendMessage

dont_spam = 2

class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=access_token,
                         prefix='!',
                         initial_channels=['hablemosdepavadaspod', 'Demian762'],
                         case_insensitive = True)
        self.rawg = rawg(rawg_url, rawg_key)
        self.steam = steam_api()
        self.dolar = precio_dolar()
        self.yt_client = build_yt_client()
        self.videos = get_videos_list(self.yt_client)
        print("Canales en vivo: " + str(self.connected_channels))
        self.s = openSocket()
        self.redes_rutina.start()
        self.programacion_rutina.start()
        sendMessage(self.s, "Hace su entrada, EL BOT DEL ESTADIO!")

    async def event_ready(self):
        print(f'Logueado a Twitch como {self.nick}.')

    @commands.command()
    async def hola(self, ctx: commands.Context):
        await ctx.send(f'Hola {ctx.author.name}!')

    @commands.command()
    async def medimela(self, ctx: commands.Context):
        hdp = ["demian762",self.nick,"hablemosdepavadaspod"]
        if ctx.author.name in hdp:
            largo = 25
        else:
            largo = int(random.uniform(1, 24))
        await ctx.send(f'A {ctx.author.name} le mide {largo} centímetros.')

    @commands.command()
    async def quiensos(self, ctx: commands.Context):
        await ctx.send(f'En realidad soy Sergio... me descubrieron.')

    @routines.routine(minutes=25, wait_first=True)
    async def redes_rutina(self):
        sendMessage(self.s, "Instagram https://www.instagram.com/hablemosdepavadas/")
        sendMessage(self.s, "YouTube https://www.youtube.com/@hablemosdepavadas")
        sendMessage(self.s, "https://www.tiktok.com/@hablemosdepavadas")

    @routines.routine(minutes=30, wait_first=True)
    async def programacion_rutina(self):
        sendMessage(self.s, "LUNES en modo fácil, gameplays completos, pero sin esfuerzo.")
        sendMessage(self.s, "MARTES de entre casa con Juan, noticias y jueguitos chill.")
        sendMessage(self.s, "MIÉRCOLES de PCMR con Demian, llevando al límite los FPS.")
        sendMessage(self.s, "VIERNES de Super Aventuras con Sergio y Juan, Aventuras gráficas con expertos en la materia.")
        sendMessage(self.s, "SÁBADOS de Contenido Retro con Ever, un viaje al pasado y la nostalgia.")
    
    @commands.command()
    async def redes(self, ctx: commands.Context):
        await ctx.send('Instagram https://www.instagram.com/hablemosdepavadas/')
        await asyncio.sleep(dont_spam)
        await ctx.send('YouTube https://www.youtube.com/@hablemosdepavadas')
        await asyncio.sleep(dont_spam)
        await ctx.send('TikTok https://www.tiktok.com/@hablemosdepavadas')
        
    @commands.command(aliases=("programación",))
    async def programacion(self, ctx: commands.Context):
        await ctx.send('LUNES en modo fácil, gameplays completos, pero sin esfuerzo.')
        await asyncio.sleep(dont_spam)
        await ctx.send('MARTES de entre casa con Juan, noticias y jueguitos chill.')
        await asyncio.sleep(dont_spam)
        await ctx.send('MIÉRCOLES de PCMR con Demian, llevando al límite los FPS.')
        await asyncio.sleep(dont_spam)
        await ctx.send('VIERNES de Super Aventuras con Sergio y Juan, Aventuras gráficas con expertos en la materia.')
        await asyncio.sleep(dont_spam)
        await ctx.send('SÁBADOS de Contenido Retro con Ever, un viaje al pasado y la nostalgia.')

    @commands.command(aliases=("cafe",))
    async def cafecito(self, ctx: commands.Context):
        await ctx.send("""Si les gusta nuestro contenido pueden ayudarnos con un cafecito
                       a https://cafecito.app/hablemosdepavadas""")

    @commands.command()
    async def info(self, ctx: commands.Context, *args):
        juego = ""
        for i in args:
            juego = juego + " " + i
        juego = juego.strip()
        nombre, puntaje = self.rawg.info(juego)
        if nombre:
            if puntaje is not None:
                await ctx.send(nombre + " tiene un puntaje de: " + str(puntaje) + " en Metacritic, según rawg.io.")
            else:
                await ctx.send(nombre + " todavía no tiene puntaje en Metacritic según rawg.io.")
            nombre_steam, precio = steam_price(nombre, self.steam, self.dolar)
            if nombre_steam:
                await ctx.send(nombre_steam + " tiene un precio en pesos de " + precio + " en Steam (con dólar tarjeta).")
            else:
                await ctx.send(f'No se encontró {nombre} en la base de datos de Steam.')
        else:
            await ctx.send(f'Escribí bien {ctx.author.name}!')

    @commands.command()
    async def puntito(self, ctx: commands.Context, nombre: str):
        nombre = nombre.lower()
        df = pd.read_csv("twitch_bot\puntitos.csv")
        if df[df["usuario"] == nombre].shape[0] == 0:
            df = df._append({"usuario":nombre,"puntos":0}, ignore_index=True)
        if ctx.author.name == "hablemosdepavadaspod":
            puntos = df.loc[df[df["usuario"] == nombre].index[0],"puntos"]
            df.loc[df[df["usuario"] == nombre].index[0],"puntos"] = puntos + 1
            await ctx.send(f'{nombre} acaba de sumar un puntito!')
        else:
            puntos = df.loc[df[df["usuario"] == nombre].index[0],"puntos"]
            df.loc[df[df["usuario"] == nombre].index[0],"puntos"] = puntos - 1
            await ctx.send(f'{nombre} acaba de perder un puntito por hacerse el vivo!')
        df.to_csv("twitch_bot\puntitos.csv", index=False)

    @commands.command()
    async def consulta(self, ctx: commands.Context):
        nombre = ctx.author.name.lower()
        df = pd.read_csv("twitch_bot\puntitos.csv")
        if df[df["usuario"] == nombre].shape[0] == 0:
            await ctx.send(f'{nombre} todavía no tiene puntitos!')
        else:
            puntitos = df[df["usuario"] == nombre]["puntos"].values[0]
            if puntitos == 1 or puntitos == -1:
                await ctx.send(f'{nombre} tiene {puntitos} puntito!')
            else:
                await ctx.send(f'{nombre} tiene {puntitos} puntitos!')

    @commands.command()
    async def recomendame(self, ctx: commands.Context):
        if len(self.videos) > 0:
            indice = random.randint(0, len(self.videos) - 1)
            video_id = self.videos.pop(indice)
            nombre_video, link_video = get_video_details(video_id, self.yt_client)
            await ctx.send(nombre_video)
            await ctx.send(link_video)
        else:
            await ctx.send("Me quedé sin recomendaciones por hoy...")

    @commands.command(aliases=("último", ))
    async def ultimo(self, ctx: commands.Context):
        video_id = get_latest_video(self.yt_client)
        nombre_video, link_video = get_video_details(video_id, self.yt_client)
        await ctx.send(nombre_video)
        await ctx.send(link_video)

    @commands.command()
    async def podcast(self, ctx: commands.Context):
        video_id = get_latest_podcast(self.yt_client)
        nombre_video, link_video = get_video_details(video_id, self.yt_client)
        await ctx.send(nombre_video)
        await ctx.send(link_video)

    @commands.command(aliases=("decision", "decisión", "desicion", "desición",))
    async def decidir(self, ctx: commands.Context, *args):
        if len(args) == 0:
            await ctx.send("""Para decidir, después del comando pasame un número,
                           la palabra moneda o las opciones que haya separadas por un espacio.""")
        elif len(args) == 1 and args[0].isdigit():
            eleccion = random.randint(1, int(args[0]))
            await ctx.send(f"Vamos por la opción {eleccion} !")
        elif len(args) == 1 and args[0] == "moneda":
            eleccion = ["CARA", "CRUZ"]
            eleccion = random.choice(eleccion)
            await ctx.send(f"Tiraste una moneda y salió {eleccion}!")
        elif len(args) == 1:
            sendMessage(self.s, f"Y bueno, elijo \"{args[0]}\", mucha opción no me diste.")
        elif len(args) > 1:
            eleccion = random.choice(list(args))
            await ctx.send(f"Me decidí por: {eleccion}")


bot = Bot()
bot.run()
