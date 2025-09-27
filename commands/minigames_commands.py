from twitchio.ext import commands
import winsound
from random import triangular, randint
from utils.logger import logger
from utils.mensaje import mensaje
from utils.puntitos_manager import funcion_puntitos
from utils.utiles_general import validate_dice_format, resource_path
from utils.configuracion import admins
from .base_command import BaseCommand

class MinigamesCommands(BaseCommand):
    def __init__(self, bot):
        super().__init__(bot)
        # Variables para el juego de margaritas
        self.margaritas = 0
        self.cuantas_margaritas = randint(1,10)
        self.ultima_margarita = None
    @commands.command(aliases=("spit","ptooie","garzo","split","escupitajo","gallo","pollo","gargajo",))
    async def escupir(self, ctx: commands.Context):
        nombre = ctx.author.name.lower()
        escupida = int(triangular(2,500,1))

        if self.bot.config.dia_semana == "Monday":
            await mensaje(f"Los Lunes no se escupe {nombre}!!")
            funcion_puntitos(nombre, cant=-1)
            await mensaje(f"{nombre} acaba de perder un puntito...")
            return

        if self.bot.config.dia_semana == "Sunday":
            await mensaje(f"Los Domingos no se escupe {nombre}!!")
            funcion_puntitos(nombre, cant=-1)
            await mensaje(f"{nombre} acaba de perder un puntito...")
            return

        if self.bot.state.ganador is not None and nombre == self.bot.state.ganador[0]:
            await mensaje(f"Vas ganando {nombre}, dejá que otros escupan!!")
            return

        if not self.bot.state.escupitajos.get(nombre):
            self.bot.state.escupitajos[nombre] = {"escupida":escupida, "count":0}
        else:
            if self.bot.state.escupitajos[nombre].get("count") >= 5:
                await mensaje(f"{nombre} se quedó sin saliva!")
                return

        self.bot.state.escupitajos[nombre]["escupida"] = escupida
        count = self.bot.state.escupitajos[nombre].get("count")
        self.bot.state.escupitajos[nombre]["count"] = count + 1
        await mensaje(f"El escupitajo de {nombre} llegó a los {escupida} centímetros!")

        if nombre in admins:
            return
        
        if self.bot.state.ganador is None:
            self.bot.state.ganador = [nombre, escupida]
            await mensaje(f"{nombre} inició el torneo de escupitajos con {escupida} cm!")
            funcion_puntitos(nombre, cant=2)
            await mensaje(f"{nombre} acaba de ganar dos puntitos!")
            return
        
        if escupida > self.bot.state.ganador[1]:
            ganador_previo = self.bot.state.ganador[0]
            self.bot.state.ganador = [nombre, escupida]
            await mensaje(f"{nombre} va ganando el torneo!")
            funcion_puntitos(nombre, cant=2)
            await mensaje(f"{nombre} acaba de ganar dos puntitos!")
            funcion_puntitos(ganador_previo, cant=-2)
            await mensaje(f"{ganador_previo} acaba de perder dos puntitos!")

    @commands.command()
    async def ganador(self, ctx: commands.Context):
        if await self.check_coma_etilico():
            return
            
        if self.bot.state.ganador is not None:
            await mensaje(f"{self.bot.state.ganador[0]} va ganando el torneo de escupitajos, con un escupitajo de {self.bot.state.ganador[1]} centímetros!")
        else:
            await ctx.send("Todavía nadie escupió!")

    @commands.command(aliases=("termina",))
    async def terminar(self, ctx: commands.Context):
        if await self.check_coma_etilico():
            return
            
        if ctx.author.name.lower() in admins and self.bot.state.ganador is not None:
            nombre = self.bot.state.ganador[0]
            await mensaje(f"{nombre} ganó el torneo de escupitajos, con un escupitajo de {self.bot.state.ganador[1]} centímetros!")
            await mensaje(f"Se reinicia el torneo!")
            self.bot.state.escupitajos = {}
            self.bot.state.ganador = None
        else:
            await mensaje("Na na na....")

    @commands.command(aliases=("dados",))
    async def dado(self, ctx: commands.Context, formato: str = None):
        if await self.check_coma_etilico():
            return
            
        autor = ctx.author.name

        if formato and formato.lower() == "porcentaje":
            resultado = randint(1, 100)
            await mensaje(f"🎲 {autor} sacó {str(resultado)} puntos de porcentaje.")
            return

        formato = validate_dice_format(formato)
        if not formato:
            await mensaje("Poné bien el dado cheee...")
            return
        
        cantidad, caras = formato.split('d')
        cantidad = int(cantidad)
        caras = int(caras)

        resultados = [randint(1, caras) for _ in range(cantidad)]
        total = sum(resultados)

        await mensaje(f"🎲 {autor} sacó {str(total)} puntos.")

    @commands.command()
    async def margarita(self, ctx: commands.Context):
        if await self.check_coma_etilico():
            return
            
        nombre = ctx.author.name
        if nombre in self.bot.admins:
            await mensaje("Los admins están sobrados de margaritas.")
            audio_path = resource_path(f"storage\margarita_3.wav")
            winsound.PlaySound(audio_path,winsound.SND_FILENAME)
            return
            
        if self.cuantas_margaritas is None:
            await mensaje(f"Basta con la margarita, {nombre}.")
            return
            
        if nombre == self.ultima_margarita:
            await mensaje(f"No no no, que pregunte otro ahora...")
            return
            
        if self.margaritas >= self.cuantas_margaritas:
            audio_path = resource_path(f"storage\margarita_2.wav")
            winsound.PlaySound(audio_path,winsound.SND_FILENAME)
            await mensaje(f"¡¡LA RECALCADA CAJETA DE TU HERMANA {nombre.upper()}!! TOMÁ TUS PUNTITOS!!")
            funcion_puntitos(nombre, cant=2)
            await mensaje(f'{nombre} acaba de sumar 2 puntitos...')
            self.cuantas_margaritas = None
        else:
            await mensaje([f"{nombre} pregunta:","¿Me regalas una margarita?"])
            if self.margaritas == 0:
                audio_path = resource_path(f"storage\margarita_1.wav")
                winsound.PlaySound(audio_path,winsound.SND_FILENAME)
            self.margaritas += 1
            self.ultima_margarita = nombre
