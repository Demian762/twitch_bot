"""
Comandos de consulta de puntos del sistema de puntaje

Este módulo proporciona comandos para que los usuarios consulten
sus puntos actuales y su puntuación histórica acumulada.

Author: Demian762
Version: 250927
"""

from twitchio.ext import commands

# Imports locales
from utils.mensaje import mensaje
from utils.puntitos_manager import consulta_puntitos, consulta_historica, consulta_victorias
from .base_command import BaseCommand

class PointsCommands(BaseCommand):
    """
    Cog para comandos de consulta de puntos
    
    Permite a los usuarios consultar su puntuación actual y acumulada
    histórica en el sistema de puntaje del bot.
    
    Attributes:
        bot: Instancia del bot principal
    """
    @commands.command(aliases=("puntos","punto","puntitos","score"))
    async def consulta(self, ctx: commands.Context):
        """
        Consulta los puntos actuales del usuario y sus victorias
        
        Muestra la puntuación actual del usuario que ejecuta el comando,
        junto con la cantidad de sorteos y torneos ganados.
        
        Args:
            ctx: Contexto del comando de Twitch
            
        Returns:
            None
            
        Example:
            !puntos -> "@usuario tiene 5 puntitos, 2 sorteos ganados y 3 torneos ganados!"
        """
        if await self.check_coma_etilico():
            return
            
        nombre = ctx.author.name
        puntitos = consulta_puntitos(nombre)
        victorias = consulta_victorias(nombre)
        
        sorteos = victorias['sorteos_ganados']
        torneos = victorias['torneos_ganados']
        
        # Construir el mensaje con manejo gramatical
        if puntitos == 0:
            mensaje_puntitos = f'@{nombre} todavía no tiene puntitos'
        elif puntitos == 1 or puntitos == -1:
            mensaje_puntitos = f'@{nombre} tiene {puntitos} puntito'
        else:
            mensaje_puntitos = f'@{nombre} tiene {puntitos} puntitos'
        
        # Agregar información de sorteos
        if sorteos == 1:
            mensaje_sorteos = f'{sorteos} sorteo ganado'
        else:
            mensaje_sorteos = f'{sorteos} sorteos ganados'
        
        # Agregar información de torneos
        if torneos == 1:
            mensaje_torneos = f'{torneos} torneo'
        else:
            mensaje_torneos = f'{torneos} torneos'
        
        # Mensaje completo: puntitos, torneos, sorteos
        mensaje_completo = f'{mensaje_puntitos}, {mensaje_torneos} y {mensaje_sorteos}!'
        await mensaje(mensaje_completo)

    @commands.command(aliases=())
    async def historico(self, ctx: commands.Context):
        """
        Consulta los puntos históricos acumulados del usuario
        
        Muestra la puntuación histórica total del usuario, que incluye
        todos los puntos ganados a lo largo del tiempo.
        
        Args:
            ctx: Contexto del comando de Twitch
            
        Returns:
            None
            
        Example:
            !historico -> "@usuario tiene 150 puntitos históricos!"
        """
        if await self.check_coma_etilico():
            return
            
        nombre = ctx.author.name
        puntitos = consulta_historica(nombre)
        if puntitos == 0:
            await ctx.send(f'@{nombre} todavía no tiene puntitos históricos!')
        elif puntitos == 1 or puntitos == -1:
            await mensaje(f'@{nombre} tiene {puntitos} puntito histórico!')
        else:
            await mensaje(f'@{nombre} tiene {puntitos} puntitos históricos!')
