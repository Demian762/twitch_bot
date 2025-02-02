import asyncio
from twitchio.ext import commands, routines
from Levenshtein import distance as lev
import winsound
from random import choice, randint, uniform, triangular, shuffle
from datetime import datetime

from utiles.api_games import *
from utiles.utiles_general import *
from utiles.puntitos_manager import *
from utiles.mensaje import *
from utiles.api_youtube import *
from utiles.secretos import (access_token, rawg_url, rawg_key)
from configuracion import *


rutina_timer = configuracion_basica.get("rutina_timer")


class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=access_token,
                         prefix='!',
                         initial_channels=['hablemosdepavadaspod', 'Demian762'],
                         case_insensitive = True)
        self.config = configuracion_basica
        self.rawg = rawg(rawg_url, rawg_key)
        self.grog_count = 0
        self.pelea = {}
        self.escupitajos = {}
        self.proteccion = False
        self.dia_semana = datetime.now().strftime('%A')
        self.margaritas = 0
        self.cuantas_margaritas = randint(1,10)
        self.ultima_margarita = None
        self.ganador = None
        self.steam = steam_api()
        self.dolar = precio_dolar()
        self.yt_client = build_yt_client()
        self.videos = get_videos_list(self.yt_client)
        self.lista_programacion = get_programacion()
        self.rutinas_counter = {"actual":0,"total":len(rutina_lista)-1}
        self.puntitos_dados = []
        self.rutinas.start()
        self.trivia_actual = None
        self.tiempo_iniciar = timer_iniciar()
        audio_path = resource_path("storage\holis.wav")
        winsound.PlaySound(audio_path,winsound.SND_FILENAME)
        sendMessage(openSocket(), "Hace su entrada, EL BOT DEL ESTADIO!")

    async def event_ready(self):
        print(f'Logueado a Twitch como {self.nick}.')

    def coma_etilico(self):
        if self.grog_count >= len(grog_list):
            return choice(coma_etilico_list)
        else:
            return False

    @commands.command(aliases=("buenas",))
    async def hola(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        nombre = ctx.author.name
        await mensaje([f"hola {nombre}!"])
        if nombre not in self.puntitos_dados:
            self.puntitos_dados.append(nombre)
            funcion_puntitos(nombre, 1)
            await mensaje(f'@{nombre.lstrip("@")} acaba de sumar un puntito!')
        else:
            await mensaje(f'Ya tenés tu puntito de hoy @{nombre.lstrip("@")}, no jodas....')


    @commands.command(aliases=("iniciotimer","reiniciartimer","timerinicio","timeriniciar","timerreiniciar",))
    async def iniciartimer(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        autor = ctx.author.name
        if autor not in admins:
            return
        self.tiempo_iniciar = timer_iniciar()
        await mensaje("¡Iniciado el cronómetro!")

    @commands.command(aliases=("timer","timerconsulta",))
    async def consultatimer(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        tiempos = timer_consulta(self.tiempo_iniciar)
        mensajes = format_time(tiempos)
        await mensaje(mensajes)

    @commands.command()
    async def chiste(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        await mensaje([f"Vos sos un chiste {ctx.author.name}."])

    @commands.command()
    async def dolar(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        await mensaje([f'El dólar tarjeta está a {self.dolar} pesos.'])

    @commands.command()
    async def medimela(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return

        if ctx.author.name in admins:
            largo = 25
        else:
            largo = int(uniform(1, 24))
        await mensaje([f'A {ctx.author.name} le mide {largo} centímetros.'])

    @commands.command()
    async def quiensos(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        await mensaje(['En realidad soy Sergio... me descubrieron.'])

    @commands.command(aliases=("salvar",))
    async def guardar(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        nombre = ctx.author.name
        msj1 = f"{nombre} quiere recordarles que...."
        msj2 = "¡¡¡GUARDEN LA PARTIDA!!!"
        await mensaje([msj1,msj2])

    @commands.command()
    async def proteccion(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        if self.proteccion == False:
            await mensaje("Aquí comienza el horario de protección al menor.")
            self.proteccion = True
        else:
            await mensaje("Aquí finaliza el horario de protección al menor.")
            self.proteccion = False

    @commands.command()
    async def spam(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        autor = ctx.author.name
        if autor not in admins:
            return
        await mensaje(spam_messenges)
        await mensaje(spam_messenges)
        await mensaje(spam_messenges)

    @commands.command()
    async def holis(self, ctx: commands.Context):
        audio_path = resource_path("storage\holis.wav")
        winsound.PlaySound(audio_path,winsound.SND_FILENAME)

    @commands.command(aliases=("helldivers","forsuperearth",))
    async def helldiver(self, ctx: commands.Context):
        audio_path = resource_path("storage\helldiver.wav")
        winsound.PlaySound(audio_path,winsound.SND_FILENAME)

    @commands.command()
    async def cuervo(self, ctx: commands.Context):
        audio_path = resource_path("storage\cuervo.wav")
        winsound.PlaySound(audio_path,winsound.SND_FILENAME)

    @commands.command(aliases=("zaraza","indyforever",))
    async def indy(self, ctx: commands.Context):
        audio_path = resource_path("storage\zazaraza.wav")
        winsound.PlaySound(audio_path,winsound.SND_FILENAME)

    @commands.command()
    async def gg(self, ctx: commands.Context):
        audio_path = resource_path("storage\piripipi.wav")
        winsound.PlaySound(audio_path,winsound.SND_FILENAME)

    @commands.command()
    async def dark(self, ctx: commands.Context):
        audio_path = resource_path("storage\dark.wav")
        winsound.PlaySound(audio_path,winsound.SND_FILENAME)

    @commands.command()
    async def quiereme(self, ctx: commands.Context):
        audio_path = resource_path("storage\quiereme.wav")
        winsound.PlaySound(audio_path,winsound.SND_FILENAME)

    @commands.command()
    async def sacrilegioso(self, ctx: commands.Context):
        audio_path = resource_path("storage\sacrilegioso.wav")
        winsound.PlaySound(audio_path,winsound.SND_FILENAME)

    @commands.command()
    async def sad(self, ctx: commands.Context):
        audio_path = resource_path("storage\sadsong.wav")
        winsound.PlaySound(audio_path,winsound.SND_FILENAME)

    @commands.command(aliases=("boca","bostero",))
    async def boque(self, ctx: commands.Context):
        audio_path = resource_path("storage\Boca.wav") # con mayuscula, no toma bien el "\b"
        await mensaje("booooooca")
        winsound.PlaySound(audio_path,winsound.SND_FILENAME)
        await mensaje(["boooooca booooooca","boca boca booooooca","booooooca boca boca"])

    @commands.command(aliases=("wansaia82","ariel",))
    async def wansaia(self, ctx: commands.Context):
        autor = ctx.author.name
        permitidos = admins + ["wansaia82"]
        if autor not in permitidos:
            return
        audio_path = resource_path("storage\wansaia82.wav")
        winsound.PlaySound(audio_path,winsound.SND_FILENAME)

    @commands.command(aliases=("redfallen","theredfallen","presta"))
    async def red(self, ctx: commands.Context):
        autor = ctx.author.name
        permitidos = admins + ["theredfallen"]
        if autor not in permitidos:
            return
        audio_path = resource_path("storage\presta.wav")
        winsound.PlaySound(audio_path,winsound.SND_FILENAME)
        await mensaje("🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈")

    @routines.routine(minutes=rutina_timer, wait_first=True)
    async def rutinas(self):
        actual = self.rutinas_counter["actual"]
        mensaje_actual = choice(rutina_lista[actual])
        await mensaje(mensaje_actual)
        if actual >= self.rutinas_counter["total"]:
            self.rutinas_counter["actual"] = 0
        else:
            self.rutinas_counter["actual"] = actual + 1

    @commands.command()
    async def redes(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        await mensaje(lista_redes)
    
    @commands.command()
    async def discord(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        await mensaje("¡Sumate a nuestro Discord! https://discord.gg/YDdPMDxFDd")
        
    @commands.command(aliases=("programación",))
    async def programacion(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        await mensaje(self.lista_programacion)

    @commands.command(aliases=("amigo",))
    async def amigos(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        await mensaje(lista_amigos)

    @commands.command(aliases=("cafe",))
    async def cafecito(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        await mensaje(cafecito_texto)

    @commands.command()
    async def info(self, ctx: commands.Context, *args):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
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
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        
        if ctx.author.name not in admins and limite > 3:
            limite = 3
        output = self.rawg.lanzamientos(limite)
        if output is not False:
            await mensaje(output)
        else:
            await mensaje("No encontré lanzamientos.")

    @commands.command(aliases="bienvenido")
    async def bienvenida(self, ctx: commands.Context, nombre: str):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        if ctx.author.name in admins:
            funcion_puntitos(nombre, 5)
            await mensaje(f'@{nombre.lstrip("@")} acaba de sumar cinco puntitos de bienvenida!')
        else:
            funcion_puntitos(nombre, -1)
            await mensaje(f'@{nombre.lstrip("@")} acaba de perder un puntito por hacerse el vivo!')

    @commands.command()
    async def puntito(self, ctx: commands.Context, nombre: str):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        if ctx.author.name in admins:
            funcion_puntitos(nombre)
            await mensaje(f'@{nombre.lstrip("@")} acaba de sumar un puntito!')
        else:
            funcion_puntitos(nombre, -1)
            await mensaje(f'@{nombre.lstrip("@")} acaba de perder un puntito por hacerse el vivo!')

    @commands.command(aliases=("puntos","punto","puntitos","score"))
    async def consulta(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        nombre = ctx.author.name
        puntitos = consulta_puntitos(nombre)
        if puntitos == 0:
            await ctx.send(f'@{nombre} todavía no tiene puntitos!')
        elif puntitos == 1 or puntitos == -1:
            await mensaje(f'@{nombre} tiene {puntitos} puntito!')
        else:
            await mensaje(f'@{nombre} tiene {puntitos} puntitos!')

    @commands.command()
    async def top(self, ctx: commands.Context, n=3):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        nombre = ctx.author.name
        if nombre in admins:
            lista = ["El top 3 de puntitos es:"]
            top = top_puntitos(n)
            lista.extend(top)
            await mensaje(lista)

    @commands.command()
    async def sorteo(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        autor = ctx.author.name
        if autor in admins:
            ganador = sorteo_puntitos()
            texto = ["¡SORTEO INICIADO!","sorteando...."]
            await mensaje(texto)
            await asyncio.sleep(randint(1,30))
            texto = ["AND THE WINNER IS:", ganador]
            await mensaje(texto)

    @commands.command()
    async def margarita(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        nombre = ctx.author.name
        if nombre in admins:
            await mensaje("Los admins están sobrados de margaritas.")
            return
        if self.cuantas_margaritas is None:
            await mensaje(f"Basta con la margarita, {nombre}.")
            return
        if nombre == self.ultima_margarita:
            await mensaje(f"No no no, que pregunte otro ahora...")
            return
        if self.margaritas >= self.cuantas_margaritas:
            await mensaje(f"¡¡LA RECALCADA CAJETA DE TU HERMANA {nombre}!! TOMÁ UN PUNTITO!!")
            funcion_puntitos(nombre)
            await mensaje(f'{nombre} acaba de sumar un puntito...')
            self.cuantas_margaritas = None
        else:
            await mensaje([f"{nombre} pregunta:","¿Me regalas una margarita?"])
            self.margaritas += 1
            self.ultima_margarita = nombre

    @commands.command()
    async def horny(self, ctx: commands.Context):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        await mensaje("yametekudasaaaaaaaai")

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

        # Comienza la pelea si todavía no lo hizo.
        if not self.pelea.get(nombre):
            self.pelea[nombre] = {"hist":[], "score": [0, 0]}
            enviar.append(f"{nombre} retó al BOT a una pelea de insultos! Debe ganarle tres veces!")

        # En caso de que la pelea esté terminada.
        if self.pelea[nombre]["score"][0] >= 3:
            await mensaje("La pelea terminó! Ya me ganaste!")
            return
        if self.pelea[nombre]["score"][1] >= 3:
            await mensaje("La pelea terminó! Fuiste derrotado!")
            return

        # Envía el primer insulto si recién empieza la pelea.
        if self.pelea[nombre]["hist"] == []:
            key = choice(list(insultos_dict.keys()))
            self.pelea[nombre]["hist"].append(key)
            enviar.append(insultos_dict.get(key))
        
        # Si la pelea ya empezó, compara la última respuesta y vuelve a insultar si hace falta.
        else:
            key = self.pelea[nombre]["hist"][-1]
            num = lev(respuestas_dict.get(key),respuesta)

            # En caso de responder bien.
            if num <= self.config.get("limite"):
                enviar.append(f"Ouch! Punto para {ctx.author.name}")
                score = self.pelea[nombre]["score"][0] + 1
                self.pelea[nombre]["score"][0] = score

                # En caso de responder bien y ganar.
                if self.pelea[nombre]["score"][0] >= 3:
                    enviar.append(f"{nombre} ganó la pelea de insultos!")
                    funcion_puntitos(nombre)
                    enviar.append(f'{nombre} acaba de sumar un puntito!')
                    await mensaje(enviar)
                    return

            # En caso de responder mal.  
            else:
                enviar.append("Ajaaa!! Punto para el BOT")
                score = self.pelea[nombre]["score"][1] + 1
                self.pelea[nombre]["score"][1] = score

                if self.pelea[nombre]["score"][1] >= 3:
                    enviar.append(f"{nombre} perdió la pelea de insultos!")
                    await mensaje(enviar)
                    return
            
            # Nuevo insulto
            while True:
                key = choice(list(insultos_dict.keys()))
                if key not in self.pelea[nombre]["hist"]:
                    break
            self.pelea[nombre]["hist"].append(key)
            enviar.append(insultos_dict.get(key))

        await mensaje(enviar)

    @commands.command(aliases=("spit","ptooie","ptooie!","garzo","split","escupitajo","gallo","pollo","gargajo",))
    async def escupir(self, ctx: commands.Context):
        nombre = ctx.author.name.lower()
        escupida = int(triangular(2,500,1))
        if self.dia_semana == "Sunday":
            await mensaje(f"Los domingos no se escupe {nombre}!!")
            funcion_puntitos(nombre, -1)
            await mensaje(f"{nombre} acaba de perder un puntito...")
            return
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
        if nombre in admins:
            return
        if self.ganador is None:
            self.ganador = [nombre, escupida]
            await mensaje(f"{nombre} inició el torneo de escupitajos con {escupida} cm!")
            return
        if escupida > self.ganador[1]:
            self.ganador = [nombre, escupida]
            await mensaje(f"{nombre} va ganando el torneo!")

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
        if ctx.author.name.lower() in admins and self.ganador is not None:
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
        votos = daddy_point()
        await mensaje(f'{ctx.author.name} acaba de votar para ver al Sugar Daddy sin camisa! Van {votos} votos!')

    @commands.command(aliases=("trivial",))
    async def trivia(self, ctx: commands.Context, *args):
        pedo = self.coma_etilico()
        if pedo is not False:
            await mensaje(pedo)
            return
        argumento = get_args(args)
        if self.trivia_actual is None and len(argumento) == 0:
            self.trivia_actual = choice(list(trivia.items()))
            await mensaje(self.trivia_actual[0])
            await asyncio.sleep(configuracion_basica.get("dont_spam"))
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
            await asyncio.sleep(configuracion_basica.get("dont_spam"))
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

bot = Bot()
bot.run()