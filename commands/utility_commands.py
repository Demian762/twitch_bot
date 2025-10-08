"""
Comandos de utilidades generales

Este módulo proporciona herramientas útiles como temporizadores,
consulta de tipo de cambio, y ayuda para tomar decisiones.

Author: Demian762
Version: 250927
"""

from twitchio.ext import commands
from random import choice, randint, uniform
from utils.logger import logger
from utils.mensaje import mensaje
from utils.utiles_general import timer_iniciar, timer_consulta, format_time
from utils.configuracion import admins
from .base_command import BaseCommand

class UtilityCommands(BaseCommand):
    """
    Cog para comandos de utilidades generales
    
    Incluye funciones de temporizador, consulta de tipo de cambio,
    y herramientas para ayudar en la toma de decisiones.
    
    Attributes:
        bot: Instancia del bot principal
    """
    @commands.command(aliases=("iniciotimer","reiniciartimer","timerinicio","timeriniciar","timerreiniciar",))
    async def iniciartimer(self, ctx: commands.Context):
        """
        Inicia o reinicia el temporizador del stream (solo admins)
        
        Args:
            ctx: Contexto del comando de Twitch
        """
        if await self.check_coma_etilico():
            return
            
        autor = ctx.author.name
        if autor not in admins:
            return
        self.bot.state.tiempo_iniciar = timer_iniciar()
        await mensaje("¡Iniciado el cronómetro!")

    @commands.command(aliases=("timer","timerconsulta","horas","tiempo"))
    async def consultatimer(self, ctx: commands.Context):
        """
        Consulta el tiempo transcurrido desde el inicio del temporizador
        
        Args:
            ctx: Contexto del comando de Twitch
        """
        if await self.check_coma_etilico():
            return
            
        tiempos = timer_consulta(self.bot.state.tiempo_iniciar)
        mensajes = format_time(tiempos)
        await mensaje(mensajes)

    @commands.command()
    async def dolar(self, ctx: commands.Context):
        """
        Consulta el tipo de cambio actual del dólar
        
        Args:
            ctx: Contexto del comando de Twitch
        """
        if await self.check_coma_etilico():
            return
        await mensaje([f'El dólar está a {self.bot.api.dolar} pesos.'])

    @commands.command(aliases=("decision", "decisión", "desicion", "desición",))
    async def decidir(self, ctx: commands.Context, *args):
        """
        Ayuda a tomar decisiones aleatorias
        
        Puede elegir números, tirar moneda o seleccionar entre opciones.
        
        Args:
            ctx: Contexto del comando de Twitch
            *args: Parámetros para la decisión
            
        Examples:
            !decidir 10 -> Elige número del 1 al 10
            !decidir moneda -> Tira una moneda (CARA/CRUZ)
            !decidir opcion1 opcion2 opcion3 -> Elige una opción
        """
        if await self.check_coma_etilico():
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
