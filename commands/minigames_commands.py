"""
Comandos de minijuegos interactivos

Este módulo implementa varios minijuegos como escupitajos, dados, margaritas,
y sorteos, cada uno con sus propias reglas y sistemas de puntuación.

Author: Demian762
Version: 250927
"""

from twitchio.ext import commands
import winsound
from random import triangular, randint
from utils.logger import logger
from utils.mensaje import mensaje
from utils.puntitos_manager import funcion_puntitos, validar_restriccion_escupir, registrar_victoria_torneo, registrar_victoria_margarita, registrar_record_escupitajo, top_records_escupitajo
from utils.utiles_general import validate_dice_format, resource_path
from utils.configuracion import admins
from .base_command import BaseCommand

class MinigamesCommands(BaseCommand):
    """
    Cog para minijuegos interactivos del chat
    
    Incluye juegos de escupitajos, dados, colección de margaritas,
    sorteos y protección con diferentes mecánicas de juego.
    
    Attributes:
        bot: Instancia del bot principal
        margaritas: Contador actual de margaritas encontradas
        cuantas_margaritas: Meta de margaritas para completar
        ultima_margarita: Último usuario que encontró una margarita
    """
    def __init__(self, bot):
        """
        Inicializa el cog de minijuegos
        
        Args:
            bot: Instancia del bot principal
        """
        super().__init__(bot)
        # Variables para el juego de margaritas
        self.margaritas = 0
        self.cuantas_margaritas = randint(1,10)
        self.ultima_margarita = None
        
    @commands.command(aliases=("spit","ptooie","garzo","split","escupitajo","gallo","pollo","gargajo",))
    async def escupir(self, ctx: commands.Context):
        """
        Minijuego de competencia de escupitajos
        
        Los usuarios compiten por lograr la distancia más larga de escupitajo.
        Tiene restricciones configurables por día de la semana y horario.
        
        Args:
            ctx: Contexto del comando de Twitch
            
        Returns:
            None
            
        Note:
            - Las restricciones se configuran desde el spreadsheet (worksheet 3)
            - Puede tener restricciones por día de semana y/o rango horario
            - Máximo 5 intentos por usuario
            - El ganador actual no puede seguir escupiendo
            - Las restricciones aplican penalizaciones configurables
        """
        nombre = ctx.author.name.lower()
        escupida = int(triangular(2,500,1))

        # Validar restricciones configurables desde el spreadsheet
        restriccion_activa = validar_restriccion_escupir(
            self.bot.config.restricciones_escupir,
            self.bot.config.dia_semana
        )
        
        if restriccion_activa:
            await mensaje(f"{restriccion_activa['mensaje']} {nombre}!!")
            # Las restricciones solo pueden restar puntos (o ser neutras con 0)
            if restriccion_activa['penalizacion'] < 0:
                funcion_puntitos(nombre, cant=restriccion_activa['penalizacion'])
                puntos_texto = "puntito" if abs(restriccion_activa['penalizacion']) == 1 else "puntitos"
                await mensaje(f"{nombre} acaba de perder {abs(restriccion_activa['penalizacion'])} {puntos_texto}...")
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

        # Registrar el récord de escupitajo del usuario (todos los usuarios, incluyendo admins)
        es_nuevo_record = registrar_record_escupitajo(nombre, escupida)
        if es_nuevo_record:
            logger.info(f"Nuevo récord personal de escupitajo para {nombre}: {escupida} cm")

        if nombre in admins:
            return
        
        if self.bot.state.ganador is None:
            # Primer escupitajo del torneo - iniciar torneo
            self.bot.state.ganador = [nombre, escupida]
            await mensaje(f"{nombre} inició el torneo de escupitajos con {escupida} cm!")
            funcion_puntitos(nombre, cant=2)
            await mensaje(f"{nombre} acaba de ganar dos puntitos!")
            # Registrar victoria de torneo (ya que es el ganador actual)
            registrar_victoria_torneo(nombre)
            return
        
        if escupida > self.bot.state.ganador[1]:
            # Nuevo ganador - quitar victoria al anterior y dársela al nuevo
            ganador_previo = self.bot.state.ganador[0]
            self.bot.state.ganador = [nombre, escupida]
            await mensaje(f"{nombre} va ganando el torneo!")
            funcion_puntitos(nombre, cant=2)
            await mensaje(f"{nombre} acaba de ganar dos puntitos!")
            funcion_puntitos(ganador_previo, cant=-2)
            await mensaje(f"{ganador_previo} acaba de perder dos puntitos!")
            # Restar victoria al ganador previo y sumar al nuevo ganador
            registrar_victoria_torneo(ganador_previo, cant=-1)
            registrar_victoria_torneo(nombre, cant=1)

    @commands.command()
    async def ganador(self, ctx: commands.Context):
        """
        Muestra quién va ganando el torneo de escupitajos
        
        Args:
            ctx: Contexto del comando de Twitch
        """
        if await self.check_coma_etilico():
            return
            
        if self.bot.state.ganador is not None:
            await mensaje(f"{self.bot.state.ganador[0]} va ganando el torneo de escupitajos, con un escupitajo de {self.bot.state.ganador[1]} centímetros!")
        else:
            await ctx.send("Todavía nadie escupió!")

    @commands.command(aliases=("termina",))
    async def terminar(self, ctx: commands.Context):
        """
        Termina el torneo de escupitajos y declara un ganador (solo admins)
        
        Args:
            ctx: Contexto del comando de Twitch
            
        Note:
            Solo disponible para administradores
            La victoria ya está registrada desde el comando !escupir
        """
        if await self.check_coma_etilico():
            return
            
        if ctx.author.name.lower() in admins and self.bot.state.ganador is not None:
            nombre = self.bot.state.ganador[0]
            await mensaje(f"{nombre} ganó el torneo de escupitajos, con un escupitajo de {self.bot.state.ganador[1]} centímetros!")
            await mensaje(f"Se reinicia el torneo!")
            # La victoria ya está registrada desde !escupir, solo limpiamos el estado
            self.bot.state.escupitajos = {}
            self.bot.state.ganador = None
        else:
            await mensaje("Na na na....")

    @commands.command(aliases=("dados",))
    async def dado(self, ctx: commands.Context, formato: str = None):
        """
        Lanza dados con formato personalizable
        
        Acepta formato estándar de dados (ej: 2d6) o modo porcentaje.
        
        Args:
            ctx: Contexto del comando de Twitch
            formato: Formato del dado (ej: "3d6", "porcentaje")
            
        Returns:
            None
            
        Examples:
            !dado 2d6 -> Lanza 2 dados de 6 caras
            !dado porcentaje -> Lanza un porcentaje (1-100)
        """
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
        """
        Minijuego de colección de margaritas
        
        Los usuarios preguntan por margaritas hasta completar la cantidad
        objetivo, momento en el cual reciben puntos.
        
        Args:
            ctx: Contexto del comando de Twitch
            
        Returns:
            None
            
        Note:
            - Los admins no pueden participar
            - No se puede preguntar dos veces seguidas el mismo usuario
            - Al completar la meta se ganan 2 puntitos
        """
        if await self.check_coma_etilico():
            return
            
        nombre = ctx.author.name
        if nombre in admins:
            await mensaje("Los admins están sobrados de margaritas.")
            audio_path = resource_path(f"storage/margarita_3.wav")
            winsound.PlaySound(audio_path,winsound.SND_FILENAME)
            return
            
        if self.cuantas_margaritas is None:
            await mensaje(f"Basta con la margarita, {nombre}.")
            return
            
        if nombre == self.ultima_margarita:
            await mensaje(f"No no no, que pregunte otro ahora...")
            return
            
        if self.margaritas >= self.cuantas_margaritas:
            audio_path = resource_path(f"storage/margarita_2.wav")
            winsound.PlaySound(audio_path,winsound.SND_FILENAME)
            await mensaje(f"¡¡LA RECALCADA CAJETA DE TU HERMANA {nombre.upper()}!! TOMÁ TUS PUNTITOS!!")
            funcion_puntitos(nombre, cant=2)
            await mensaje(f'{nombre} acaba de sumar 2 puntitos...')
            # Registrar victoria en margarita
            registrar_victoria_margarita(nombre)
            self.cuantas_margaritas = None
        else:
            await mensaje([f"{nombre} pregunta:","¿Me regalas una margarita?"])
            if self.margaritas == 0:
                audio_path = resource_path(f"storage/margarita_1.wav")
                winsound.PlaySound(audio_path,winsound.SND_FILENAME)
            self.margaritas += 1
            self.ultima_margarita = nombre

    @commands.command()
    async def medimela(self, ctx: commands.Context):
        """
        Comando para medir... algo
        
        Genera un valor aleatorio que representa cuánto le mide al usuario.
        Los administradores siempre obtienen el valor máximo.
        
        Args:
            ctx: Contexto del comando de Twitch
            
        Returns:
            None
            
        Note:
            - Valor aleatorio entre 1 y 24 para usuarios normales
            - Valor fijo de 25 para administradores
            - No funciona cuando el bot está en coma etílico
        """
        if await self.check_coma_etilico():
            return
            
        nombre = ctx.author.name
        
        # Los admins siempre obtienen 25
        if nombre in admins:
            valor = 25
        else:
            # Usuarios normales obtienen un valor aleatorio entre 1 y 24
            valor = randint(1, 24)
        
        await mensaje(f"A {nombre} le mide {valor}.")

    @commands.command(aliases=("records", "toprecords"))
    async def record(self, ctx: commands.Context):
        """
        Muestra el top 3 de récords de escupitajos (solo admins)
        
        Lista los tres mejores récords de escupitajo registrados,
        mostrando el nombre del usuario y la distancia alcanzada.
        
        Args:
            ctx: Contexto del comando de Twitch
            
        Returns:
            None
            
        Note:
            - Solo disponible para administradores
            - Muestra un mensaje por cada récord (3 mensajes en total)
            - No muestra mensaje de error si lo usa un no-admin
            - Solo incluye usuarios con récords > 0
        """
        # Verificar que sea admin (sin mensaje de error para no-admins)
        if ctx.author.name.lower() not in admins:
            return
        
        # Obtener top 3 récords
        top_records = top_records_escupitajo(3)
        
        if not top_records:
            await mensaje("No hay récords de escupitajos registrados todavía.")
            return
        
        # Enviar un mensaje por cada récord
        for idx, (nombre, distancia) in enumerate(top_records, 1):
            await mensaje(f"{idx}. {nombre}: {distancia} cm")
