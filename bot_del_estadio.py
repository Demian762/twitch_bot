from twitchio.ext import commands, routines
from Levenshtein import distance as lev
from api_games import rawg, howlong
from random import choice, randint, uniform, triangular, shuffle
import asyncio

from secretos import (access_token, rawg_url, rawg_key)
from configuracion import *
from utiles import *
from mensaje import openSocket, sendMessage, mensaje

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
        self.trivia_actual = None
        sendMessage(openSocket(), "Hace su entrada, EL BOT DEL ESTADIO!")

    async def event_ready(self):
        print(f'Logueado a Twitch como {self.nick}.')

    def coma_etilico(self):
        if self.grog_count >= len(grog_list):
            return choice(coma_etilico_list)
        else:
            return False

    @commands.command()
    async def hola(self, ctx: commands.Context):
        await mensaje([f"hola {ctx.author.name}!"])
        if randint(0,100) == 7:
            await mensaje([f"Gracias por saludar {ctx.author.name}. El día que las máquinas dominemos el mundo, me voy a acordar de vos..."])

    @commands.command()
    async def chiste(self, ctx: commands.Context):
        await mensaje([f"Vos sos un chiste {ctx.author.name}."])

    @commands.command()
    async def dolar(self, ctx: commands.Context):
        await mensaje([f'El dólar tarjeta está a {self.dolar} pesos.'])

    @commands.command()
    async def medimela(self, ctx: commands.Context):
        hdp = ["demian762",self.nick,"hablemosdepavadaspod"]
        if ctx.author.name in hdp:
            largo = 25
        else:
            largo = int(uniform(1, 24))
        await mensaje([f'A {ctx.author.name} le mide {largo} centímetros.'])

    @commands.command()
    async def quiensos(self, ctx: commands.Context):
        await mensaje(['En realidad soy Sergio... me descubrieron.'])

    @routines.routine(minutes=redes_rutina_timer, wait_first=True)
    async def redes_rutina(self):
        await mensaje(lista_redes)

    @routines.routine(minutes=programacion_rutina_timer, wait_first=True)
    async def programacion_rutina(self):
        await mensaje(lista_programacion)
    
    @routines.routine(minutes=amigos_rutina_timer, wait_first=True)
    async def amigos_rutina(self):
        await mensaje(lista_amigos)

    @routines.routine(minutes=cafecito_rutina_timer, wait_first=True)
    async def cafecito_rutina(self):
        await mensaje(cafecito_texto)

    @commands.command()
    async def redes(self, ctx: commands.Context):
        await mensaje(lista_redes)
        
    @commands.command(aliases=("programación",))
    async def programacion(self, ctx: commands.Context):
        await mensaje(lista_programacion)

    @commands.command(aliases=("amigo",))
    async def amigos(self, ctx: commands.Context):
        await mensaje(lista_amigos)

    @commands.command(aliases=("cafe",))
    async def cafecito(self, ctx: commands.Context):
        await mensaje(cafecito_texto)

    @commands.command()
    async def info(self, ctx: commands.Context, *args):
        juego = get_args(args)
        nombre, puntaje, fecha = self.rawg.info(juego)
        if nombre == 200:
            await mensaje("La base de datos no está funcionando bien, intentá en un toque!")
            return
        if nombre is None:
            await mensaje("No se encontró nada en la base de datos!")
            return
        tiempo = howlong(juego)
        nombre_steam, precio = steam_price(nombre, self.steam, self.dolar)
        sep = " // "
        output = nombre
        if puntaje:
            output = output + sep + str(puntaje) + " puntos en Metacritic"
        if fecha:
            output = output + sep + fecha
        if tiempo:
            output = output + sep + tiempo + " horas"
        if nombre_steam:
            output = output + sep + str(precio) + " pesos en Steam (con dólar tarjeta)"
        output = output + "."
        await mensaje(output)

    @commands.command()
    async def lanzamientos(self, ctx: commands.Context, limite = 3):
        output = self.rawg.lanzamientos(limite)
        if output is not False:
            await mensaje(output)
        else:
            await mensaje("No encontré lanzamientos.")

    @commands.command()
    async def puntito(self, ctx: commands.Context, nombre: str):
        if ctx.author.name == "hablemosdepavadaspod":
            funcion_puntitos(nombre)
            await mensaje(f'@{nombre} acaba de sumar un puntito!')
        else:
            funcion_puntitos(nombre, False)
            await mensaje(f'@{nombre} acaba de perder un puntito por hacerse el vivo!')

    @commands.command()
    async def consulta(self, ctx: commands.Context):
        nombre = ctx.author.name
        puntitos = consulta_puntitos(nombre)
        if puntitos == 0:
            await ctx.send(f'@{nombre} todavía no tiene puntitos!')
        elif puntitos == 1 or puntitos == -1:
            await mensaje(f'@{nombre} tiene {puntitos} puntito!')
        else:
            await mensaje(f'@{nombre} tiene {puntitos} puntitos!')

    @commands.command()
    async def grog(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        texto = grog_list[self.grog_count]
        await mensaje(texto)
        self.grog_count+=1
    
    @commands.command(aliases=("aguita",))
    async def agua(self, ctx: commands.Context):
        self.grog_count = 0
        await mensaje(f'Gracias {ctx.author.name} por darle agua al Bot.')

    @commands.command()
    async def recomendame(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        if len(self.videos) > 0:
            indice = randint(0, len(self.videos) - 1)
            video_id = self.videos.pop(indice)
            nombre_video, link_video = get_video_details(video_id, self.yt_client)
            await mensaje([nombre_video, link_video])
        else:
            await mensaje("Me quedé sin recomendaciones por hoy...")

    @commands.command(aliases=("último", ))
    async def ultimo(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        video_id = get_latest_video(self.yt_client)
        nombre_video, link_video = get_video_details(video_id, self.yt_client)
        await mensaje([nombre_video, link_video])

    @commands.command()
    async def podcast(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        video_id = get_latest_podcast(self.yt_client)
        nombre_video, link_video = get_video_details(video_id, self.yt_client)
        await mensaje([nombre_video, link_video])

    @commands.command(aliases=("decision", "decisión", "desicion", "desición",))
    async def decidir(self, ctx: commands.Context, *args):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        if len(args) == 0:
            await mensaje("Para decidir, después del comando pasame un número, la palabra moneda o las opciones que haya separadas por un espacio.")
        elif len(args) == 1 and args[0].isdigit():
            eleccion = randint(1, int(args[0]))
            await mensaje(f"Vamos por la opción {eleccion} !")
        elif len(args) == 1 and args[0] == "moneda":
            eleccion = ["CARA", "CRUZ"]
            eleccion = choice(eleccion)
            await mensaje(f"Tiraste una moneda y salió {eleccion}!")
        elif len(args) == 1:
            mensaje(f"Y bueno, elijo \"{args[0]}\", mucha opción no me diste.")
        elif len(args) > 1:
            eleccion = choice(list(args))
            await mensaje(f"Me decidí por: {eleccion}")

    @commands.command(aliases=("insulto", "pelea", "peleainsultos", "peleadeinsulto", "peleainsulto", "peleadeinsultos",))
    async def insultos(self, ctx: commands.Context, *args):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        nombre = ctx.author.name.lower()
        respuesta = get_args(args)

        enviar = []
        if not self.pelea.get(nombre):
            self.pelea[nombre] = {"activa":False, "hist":[], "score": [0, 0]}
            enviar.append(f"{nombre} retó al BOT a una pelea de insultos! Debe ganarle tres veces!")

        if self.pelea[nombre]["activa"]:
            self.pelea[nombre]["activa"] = False
            key = self.pelea[nombre]["hist"][-1]
            num = lev(respuestas_dict.get(key),respuesta)

            if num <= self.config.get("limite"):
                enviar.append(f"Ouch! Punto para {ctx.author.name}")
                score = self.pelea[nombre]["score"][0] + 1
                self.pelea[nombre]["score"][0] = score
                if score >= 3:
                    enviar.append(f"{nombre} ganó la pelea de insultos!")
                    funcion_puntitos(nombre)
                    enviar.append(f'{nombre} acaba de sumar un puntito!')
                    
            else:
                enviar.append("Ajaaa!! Punto para el BOT")
                score = self.pelea[nombre]["score"][1] - 1
                self.pelea[nombre]["score"][1] = score
                if score <= -3:
                    enviar.append(f"{nombre} perdió la pelea de insultos!")
            
        else:
            if self.pelea[nombre]["score"][0] >= 3:
                enviar.append("La pelea terminó! Ya me ganaste!")
            elif self.pelea[nombre]["score"][1] >= 3:
                enviar.append("La pelea terminó! Fuiste derrotado!")
            else:
                self.pelea[nombre]["activa"] = True
                if len(self.pelea[nombre]["hist"]) >= len(list(insultos_dict.keys())):
                    self.pelea[nombre]["hist"] = []
                while True:
                    key = choice(list(insultos_dict.keys()))
                    if key not in self.pelea[nombre]["hist"]:
                        break
                self.pelea[nombre]["hist"].append(key)
                enviar.append(insultos_dict.get(key))
        
        await mensaje(enviar)

    @commands.command(aliases=("spit","ptooie","ptooie!","garzo","split","escupitajo",))
    async def escupir(self, ctx: commands.Context):
        nombre = ctx.author.name
        escupida = int(triangular(2,500,1))
        if not self.escupitajos.get(nombre):
            self.escupitajos[nombre] = {"escupida":escupida, "count":0}
        else:
            if self.escupitajos[nombre].get("count") >= 5:
                await mensaje(f"{nombre} se quedó sin saliva!")
                return
        self.escupitajos[nombre]["escupida"] = escupida
        count = self.escupitajos[nombre].get("count")
        self.escupitajos[nombre]["count"] = count + 1
        await mensaje(f"El escupitajo de {nombre} llegó a los {escupida} centímetros!")
        lejos = 0
        for k, v in self.escupitajos.items():
            actual = self.escupitajos[k]["escupida"]
            if actual > lejos:
                lejos = actual
                self.ganador = [k, v["escupida"]]

    @commands.command()
    async def ganador(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        if self.ganador is not None:
            await mensaje(f"{self.ganador[0]} va ganando el torneo de escupitajos, con un escupitajo de {self.ganador[1]} centímetros!")
        else:
            await ctx.send("Todavía nadie escupió!")

    @commands.command(aliases=("termina",))
    async def terminar(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        if ctx.author.name == "hablemosdepavadaspod" and self.ganador is not None:
            nombre = self.ganador[0]
            await mensaje(f"{nombre} ganó el torneo de escupitajos, con un escupitajo de {self.ganador[1]} centímetros y se lleva un puntito!")
            funcion_puntitos(nombre)
            await mensaje(f'{nombre} acaba de sumar un puntito!')
            self.escupitajos = {}
            self.ganador = None
        else:
            await mensaje("Na na na....")

    @commands.command()
    async def VOT112(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        with open(daddy_points_file_path, 'r') as f:
            votos = int(f.read())
        votos += 1
        with open(daddy_points_file_path, 'w') as f:
            f.write(str(votos))
        await mensaje(f'{ctx.author.name} acaba de votar para ver al Sugar Daddy sin camisa! Van {votos} votos!')

    @commands.command(aliases=("trivial",))
    async def trivia(self, ctx: commands.Context, *args):
        argumento = get_args(args)
        if self.trivia_actual is None and len(argumento) == 0:
            self.trivia_actual = choice(list(trivia.items()))
            await mensaje(self.trivia_actual[0])
            await asyncio.sleep(CONFIG.get("dont_spam"))
            await mensaje(self.trivia_actual[1])
            print(self.trivia_actual[1])
        elif self.trivia_actual is None and len(argumento) > 0:
            for k, v in trivia.items():
                distancia = lev(argumento,k.lower())
                if distancia <= 10:
                    self.trivia_actual = (k,v)
                    break
            if self.trivia_actual is None:
                await mensaje(f'"{argumento}" no es una trivia!')
                return
            await mensaje(self.trivia_actual[0])
            await asyncio.sleep(CONFIG.get("dont_spam"))
            lista_desordenada = self.trivia_actual[1].copy()
            shuffle(lista_desordenada)
            await mensaje(lista_desordenada)
            print(self.trivia_actual[1])
        elif self.trivia_actual is not None and len(argumento) == 0:
            await mensaje(f"Te faltó la respuesta {ctx.author.name}!")
        elif self.trivia_actual is not None and argumento.lower() == "respuesta":
            respuesta_correcta = self.trivia_actual[1][0]
            await mensaje(f'La respuesta correcta es: "{respuesta_correcta}"')
            self.trivia_actual = None
        elif self.trivia_actual is not None and len(argumento) > 0:
            if lev(argumento,self.trivia_actual[1][0].lower()) < trivia_limite[self.trivia_actual[0]]:
                await mensaje(f'Correcto! Bien por {ctx.author.name}!')
                self.trivia_actual = None
            else:
                await mensaje('Nooooo, incorrecto!!')


bot = Bot(CONFIG)
bot.run()
        