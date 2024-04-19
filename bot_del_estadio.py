from twitchio.ext import commands, routines
from Levenshtein import distance as lev
from rawgio import rawg
import pandas as pd
from random import choice, randint, uniform, triangular
import asyncio

from secretos import (access_token, rawg_url, rawg_key)
from configuracion import CONFIG
from utiles import *
from mensaje import openSocket, sendMessage

spam_intensity = CONFIG.get("spam_intensity")
redes_rutina_timer = CONFIG.get("redes_rutina_timer") * (1/spam_intensity)
programacion_rutina_timer = CONFIG.get("programacion_rutina_timer") * (1/spam_intensity)
amigos_rutina_timer = CONFIG.get("amigos_rutina_timer") * (1/spam_intensity)
cafecito_rutina_timer = CONFIG.get("cafecito_rutina_timer") * (1/spam_intensity)


class Bot(commands.Bot):

    def __init__(self, CONFIG):
        super().__init__(token=access_token,
                         prefix='!',
                         initial_channels=['hablemosdepavadaspod', 'Demian762'],
                         case_insensitive = True)
        self.config = CONFIG
        self.rawg = rawg(rawg_url, rawg_key)
        self.grog_count = 0
        self.pelea = {}
        self.escupitajos = {}
        self.ganador = None
        self.steam = steam_api()
        self.dolar = precio_dolar()
        self.yt_client = build_yt_client()
        self.videos = get_videos_list(self.yt_client)
        print("Canales en vivo: " + str(self.connected_channels))
        self.redes_rutina.start()
        self.programacion_rutina.start()
        self.amigos_rutina.start()
        self.cafecito_rutina.start()
        sendMessage(openSocket(), "Hace su entrada, EL BOT DEL ESTADIO!")

    async def event_ready(self):
        print(f'Logueado a Twitch como {self.nick}.')

    @commands.command()
    async def hola(self, ctx: commands.Context):
        await ctx.send(f'Hola {ctx.author.name}!')

    @commands.command()
    async def chiste(self, ctx: commands.Context):
        await ctx.send(f'Vos sos un chiste {ctx.author.name}.')

    @commands.command()
    async def dolar(self, ctx: commands.Context):
        await ctx.send(f'El dólar tarjeta está a {self.dolar} pesos.')

    @commands.command()
    async def medimela(self, ctx: commands.Context):
        hdp = ["demian762",self.nick,"hablemosdepavadaspod"]
        if ctx.author.name in hdp:
            largo = 25
        else:
            largo = int(uniform(1, 24))
        await ctx.send(f'A {ctx.author.name} le mide {largo} centímetros.')

    @commands.command()
    async def quiensos(self, ctx: commands.Context):
        await ctx.send(f'En realidad soy Sergio... me descubrieron.')

    @routines.routine(minutes=redes_rutina_timer, wait_first=True)
    async def redes_rutina(self):
        s = openSocket()
        sendMessage(s, "Nuestras REDES:")
        await asyncio.sleep(self.config.get("dont_spam"))
        sendMessage(s, "Instagram https://www.instagram.com/hablemosdepavadas/")
        await asyncio.sleep(self.config.get("dont_spam"))
        sendMessage(s, "YouTube https://www.youtube.com/@hablemosdepavadas")
        await asyncio.sleep(self.config.get("dont_spam"))
        sendMessage(s, "TikTok https://www.tiktok.com/@hablemosdepavadas")
        await asyncio.sleep(self.config.get("dont_spam"))
        sendMessage(s, 'Spotify https://open.spotify.com/show/2sC1753wCmhBnDkZx7UOyj')

    @routines.routine(minutes=programacion_rutina_timer, wait_first=True)
    async def programacion_rutina(self):
        s = openSocket()
        sendMessage(s, "Nuestra PROGRAMACIÓN:")
        await asyncio.sleep(self.config.get("dont_spam"))
        sendMessage(s, "LUNES en modo fácil, gameplays completos, pero sin esfuerzo.")
        await asyncio.sleep(self.config.get("dont_spam"))
        sendMessage(s, "MARTES de entre casa con Juan, noticias y jueguitos chill.")
        await asyncio.sleep(self.config.get("dont_spam"))
        sendMessage(s, "MIÉRCOLES de PCMR con Demian, llevando al límite los FPS.")
        await asyncio.sleep(self.config.get("dont_spam"))
        sendMessage(s, "VIERNES de Super Aventuras con Sergio y Juan, Aventuras gráficas con expertos en la materia.")
        await asyncio.sleep(self.config.get("dont_spam"))
        sendMessage(s, "SÁBADOS de Contenido Retro con Ever, un viaje al pasado y la nostalgia.")
    
    @routines.routine(minutes=amigos_rutina_timer, wait_first=True)
    async def amigos_rutina(self):
        s = openSocket()
        sendMessage(s, "Nuestros AMIGOS:")
        await asyncio.sleep(self.config.get("dont_spam"))
        sendMessage(s, "Point and Click Store https://www.instagram.com/pointandclickstore/")
        await asyncio.sleep(self.config.get("dont_spam"))
        sendMessage(s, "POPLAND customs https://www.instagram.com/poplandcustoms/")
        await asyncio.sleep(self.config.get("dont_spam"))
        sendMessage(s, "Tobi Oulego https://www.instagram.com/toubi_/")


    @routines.routine(minutes=cafecito_rutina_timer, wait_first=True)
    async def cafecito_rutina(self):
        s = openSocket()
        sendMessage(s, "Si les gusta nuestro contenido pueden ayudarnos con un cafecito a https://cafecito.app/hablemosdepavadas")

    @commands.command()
    async def redes(self, ctx: commands.Context):
        await ctx.send('Instagram https://www.instagram.com/hablemosdepavadas/')
        await asyncio.sleep(self.config.get("dont_spam"))
        await ctx.send('YouTube https://www.youtube.com/@hablemosdepavadas')
        await asyncio.sleep(self.config.get("dont_spam"))
        await ctx.send('TikTok https://www.tiktok.com/@hablemosdepavadas')
        await asyncio.sleep(self.config.get("dont_spam"))
        await ctx.send('Spotify https://open.spotify.com/show/2sC1753wCmhBnDkZx7UOyj')
        
    @commands.command(aliases=("programación",))
    async def programacion(self, ctx: commands.Context):
        await ctx.send('LUNES en modo fácil, gameplays completos, pero sin esfuerzo.')
        await asyncio.sleep(self.config.get("dont_spam"))
        await ctx.send('MARTES de entre casa con Juan, noticias y jueguitos chill.')
        await asyncio.sleep(self.config.get("dont_spam"))
        await ctx.send('MIÉRCOLES de PCMR con Demian, llevando al límite los FPS.')
        await asyncio.sleep(self.config.get("dont_spam"))
        await ctx.send('VIERNES de Super Aventuras con Sergio y Juan, Aventuras gráficas con expertos en la materia.')
        await asyncio.sleep(self.config.get("dont_spam"))
        await ctx.send('SÁBADOS de Contenido Retro con Ever, un viaje al pasado y la nostalgia.')

    @commands.command(aliases=("amigo",))
    async def amigos(self, ctx: commands.Context):
        await ctx.send('Point and Click Store https://www.instagram.com/pointandclickstore/')
        await asyncio.sleep(self.config.get("dont_spam"))
        await ctx.send('POPLAND customs https://www.instagram.com/poplandcustoms/')
        await asyncio.sleep(self.config.get("dont_spam"))
        await ctx.send('Tobi Oulego https://www.instagram.com/toubi_/')

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
        nombre, puntaje, fecha, tiempo = self.rawg.info(juego)
        nombre_steam, precio = steam_price(nombre, self.steam, self.dolar)
        sep = " // "
        if nombre is not False:
            output = nombre
        else:
            await ctx.send(f'Escribí bien {ctx.author.name}!')
            return
        if puntaje:
            output = output + sep + str(puntaje) + " puntos en Metacritic"
        if fecha:
            output = output + sep + fecha
        if tiempo != 0:
            output = output + sep + str(tiempo) + " horas"
        if nombre_steam:
            output = output + sep + str(precio) + " pesos en Steam (con dólar tarjeta)"
        output = output + "."
        await ctx.send(output)

    @commands.command()
    async def lanzamientos(self, ctx: commands.Context, limite = 3):
        output = self.rawg.lanzamientos(limite)
        for game in output:
            await ctx.send(game)
            await asyncio.sleep(self.config.get("dont_spam"))

    @commands.command()
    async def puntito(self, ctx: commands.Context, nombre: str):
        nombre = nombre.lower().lstrip("@")
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
            await ctx.send(f'@{nombre} todavía no tiene puntitos!')
        else:
            puntitos = df[df["usuario"] == nombre]["puntos"].values[0]
            if puntitos == 1 or puntitos == -1:
                await ctx.send(f'@{nombre} tiene {puntitos} puntito!')
            else:
                await ctx.send(f'@{nombre} tiene {puntitos} puntitos!')

    @commands.command()
    async def grog(self, ctx: commands.Context):
        if self.grog_count >= len(grog_list):
            await ctx.send('El Bot está en coma etílico...')
            return
        mensaje = grog_list[self.grog_count]
        await ctx.send(mensaje)
        self.grog_count+=1
    
    @commands.command(aliases=("aguita",))
    async def agua(self, ctx: commands.Context):
        if self.grog_count > 0:
            self.grog_count = 0
            await ctx.send(f'Gracias {ctx.author.name} por darle agua al Bot.')

    @commands.command()
    async def recomendame(self, ctx: commands.Context):
        if self.grog_count >= len(grog_list):
            await ctx.send('El Bot está en coma etílico y no puede recomendar nada...')
            return
        if len(self.videos) > 0:
            indice = randint(0, len(self.videos) - 1)
            video_id = self.videos.pop(indice)
            nombre_video, link_video = get_video_details(video_id, self.yt_client)
            await ctx.send(nombre_video)
            await ctx.send(link_video)
        else:
            await ctx.send("Me quedé sin recomendaciones por hoy...")

    @commands.command(aliases=("último", ))
    async def ultimo(self, ctx: commands.Context):
        if self.grog_count >= len(grog_list):
            await ctx.send('El Bot está en coma etílico y no puede buscar cosas en YouTube...')
            return
        video_id = get_latest_video(self.yt_client)
        nombre_video, link_video = get_video_details(video_id, self.yt_client)
        await ctx.send(nombre_video)
        await ctx.send(link_video)

    @commands.command()
    async def podcast(self, ctx: commands.Context):
        if self.grog_count >= len(grog_list):
            await ctx.send('El Bot está en coma etílico y no puede buscar cosas en YouTube...')
            return
        video_id = get_latest_podcast(self.yt_client)
        nombre_video, link_video = get_video_details(video_id, self.yt_client)
        await ctx.send(nombre_video)
        await ctx.send(link_video)

    @commands.command(aliases=("decision", "decisión", "desicion", "desición",))
    async def decidir(self, ctx: commands.Context, *args):
        if self.grog_count >= len(grog_list):
            await ctx.send("El BOT está en pedo y no puede decidir nada.")
            return
        if len(args) == 0:
            await ctx.send("""Para decidir, después del comando pasame un número,
                           la palabra moneda o las opciones que haya separadas por un espacio.""")
        elif len(args) == 1 and args[0].isdigit():
            eleccion = randint(1, int(args[0]))
            await ctx.send(f"Vamos por la opción {eleccion} !")
        elif len(args) == 1 and args[0] == "moneda":
            eleccion = ["CARA", "CRUZ"]
            eleccion = choice(eleccion)
            await ctx.send(f"Tiraste una moneda y salió {eleccion}!")
        elif len(args) == 1:
            sendMessage(self.s, f"Y bueno, elijo \"{args[0]}\", mucha opción no me diste.")
        elif len(args) > 1:
            eleccion = choice(list(args))
            await ctx.send(f"Me decidí por: {eleccion}")

    @commands.command(aliases=("insulto", "pelea", "peleainsultos", "peleadeinsulto", "peleainsulto", "peleadeinsultos",))
    async def insultos(self, ctx: commands.Context, *args):
        if self.grog_count >= len(grog_list):
            await ctx.send("El BOT está en pedo y no puede insultar a nadie.")
            return
        nombre = ctx.author.name.lower()

        respuesta = ""
        for i in args:
            respuesta = respuesta + " " + i
        respuesta = respuesta.strip()

        if not self.pelea.get(nombre):
            self.pelea[nombre] = {"activa":False, "hist":[], "score": [0, 0]}
            await ctx.send(f"{nombre} retó al BOT a una pelea de insultos! Debe ganarle tres veces!")
            await asyncio.sleep(self.config.get("dont_spam"))

        if self.pelea[nombre]["activa"]:
            self.pelea[nombre]["activa"] = False
            key = self.pelea[nombre]["hist"][-1]
            num = lev(respuestas_dict.get(key),respuesta)

            if num <= self.config.get("limite"):
                await ctx.send(f"Ouch! Punto para {ctx.author.name}")
                score = self.pelea[nombre]["score"][0] + 1
                self.pelea[nombre]["score"][0] = score
                if score >= 3:
                    await asyncio.sleep(self.config.get("dont_spam"))
                    await ctx.send(f"{nombre} ganó la pelea de insultos!")
                    df = pd.read_csv("twitch_bot\puntitos.csv")
                    if df[df["usuario"] == nombre].shape[0] == 0:
                        df = df._append({"usuario":nombre,"puntos":0}, ignore_index=True)
                    puntos = df.loc[df[df["usuario"] == nombre].index[0],"puntos"]
                    df.loc[df[df["usuario"] == nombre].index[0],"puntos"] = puntos + 1
                    df.to_csv("twitch_bot\puntitos.csv", index=False)
                    await asyncio.sleep(self.config.get("dont_spam"))
                    await ctx.send(f'{nombre} acaba de sumar un puntito!')
                    
            else:
                await ctx.send("Ajaaa!! Punto para el BOT")
                score = self.pelea[nombre]["score"][1] - 1
                self.pelea[nombre]["score"][1] = score
                if score <= -3:
                    await asyncio.sleep(self.config.get("dont_spam"))
                    await ctx.send(f"{nombre} perdió la pelea de insultos!")
            
        else:
            if self.pelea[nombre]["score"][0] >= 3:
                await ctx.send("La pelea terminó! Ya me ganaste!")
            elif self.pelea[nombre]["score"][1] >= 3:
                await ctx.send("La pelea terminó! Fuiste derrotado!")
            else:
                self.pelea[nombre]["activa"] = True
                if len(self.pelea[nombre]["hist"]) >= len(list(insultos_dict.keys())):
                    self.pelea[nombre]["hist"] = []
                while True:
                    key = choice(list(insultos_dict.keys()))
                    if key not in self.pelea[nombre]["hist"]:
                        break
                self.pelea[nombre]["hist"].append(key)
                await ctx.send(insultos_dict.get(key))

    @commands.command(aliases=("spit","ptooie","ptooie!","garzo",))
    async def escupir(self, ctx: commands.Context):
        nombre = ctx.author.name
        escupida = int(triangular(2,500,1))
        if not self.escupitajos.get(nombre):
            self.escupitajos[nombre] = {"escupida":escupida, "count":0}
        else:
            if self.escupitajos[nombre].get("count") >= 5:
                await ctx.send(f"{nombre} se quedó sin saliva!")
                return
        self.escupitajos[nombre]["escupida"] = escupida
        count = self.escupitajos[nombre].get("count")
        self.escupitajos[nombre]["count"] = count + 1
        await ctx.send(f"El escupitajo de {nombre} llegó a los {escupida} centímetros!")
        lejos = 0
        for k, v in self.escupitajos.items():
            actual = self.escupitajos[k]["escupida"]
            if actual > lejos:
                lejos = actual
                self.ganador = [k, v["escupida"]]

    @commands.command()
    async def ganador(self, ctx: commands.Context):
        if self.ganador is not None:
            await ctx.send(f"""{self.ganador[0]} va ganando el torneo de escupitajos,
                           con un escupitajo de {self.ganador[1]} centímetros!""")
        else:
            await ctx.send("Todavía nadie escupió!")

    @commands.command(aliases=("termina",))
    async def terminar(self, ctx: commands.Context):
        if ctx.author.name == "hablemosdepavadaspod" and self.ganador is not None:
            nombre = self.ganador[0]
            await ctx.send(f"""{nombre} ganó el torneo de escupitajos,
                con un escupitajo de {self.ganador[1]} centímetros!
                Se lleva un puntito y se reinicia el torneo! """)
            df = pd.read_csv("twitch_bot\puntitos.csv")
            if df[df["usuario"] == nombre].shape[0] == 0:
                df = df._append({"usuario":nombre,"puntos":0}, ignore_index=True)
            puntos = df.loc[df[df["usuario"] == nombre].index[0],"puntos"]
            df.loc[df[df["usuario"] == nombre].index[0],"puntos"] = puntos + 1
            await ctx.send(f'{nombre} acaba de sumar un puntito!')
            df.to_csv("twitch_bot\puntitos.csv", index=False)
            self.escupitajos = {}
            self.ganador = None
        else:
            await ctx.send("Na na na....")


bot = Bot(CONFIG)
bot.run()
        