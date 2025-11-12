"""
Comandos de consulta de puntos del sistema de puntaje

Este módulo proporciona comandos para que los usuarios consulten
sus puntos actuales y su puntuación histórica acumulada.

Author: Demian762
Version: 250927
"""

from twitchio.ext import commands
from random import choice

# Imports locales
from utils.mensaje import mensaje
from utils.puntitos_manager import consulta_puntitos, consulta_historica, consulta_victorias, funcion_puntitos
from utils.configuracion import admins
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
        junto con la cantidad de sorteos, torneos, timbas y margaritas ganadas.
        
        Args:
            ctx: Contexto del comando de Twitch
            
        Returns:
            None
            
        Example:
            !puntos -> "@usuario tiene 5 puntitos, 3 torneos, 2 sorteos ganados, 1 timba y 4 margaritas!"
        """
        if await self.check_coma_etilico():
            return
            
        nombre = ctx.author.name
        puntitos = consulta_puntitos(nombre)
        victorias = consulta_victorias(nombre)
        
        sorteos = victorias['sorteos_ganados']
        torneos = victorias['torneos_ganados']
        timbas = victorias['timbas_ganadas']
        margaritas = victorias['margaritas_ganadas']
        escupitajo_record = victorias['escupitajo_record']
        
        # Construir el mensaje con manejo gramatical
        if puntitos == 0:
            mensaje_puntitos = f'@{nombre} todavía no tiene puntitos'
        elif puntitos == 1 or puntitos == -1:
            mensaje_puntitos = f'@{nombre} tiene {puntitos} puntito'
        else:
            mensaje_puntitos = f'@{nombre} tiene {puntitos} puntitos'
        
        # Lista de estadísticas a mostrar (solo las que sean > 0)
        estadisticas = []
        
        # Agregar información de torneos solo si > 0
        if torneos > 0:
            if torneos == 1:
                estadisticas.append(f'{torneos} torneo')
            else:
                estadisticas.append(f'{torneos} torneos')
        
        # Agregar información de sorteos solo si > 0
        if sorteos > 0:
            if sorteos == 1:
                estadisticas.append(f'{sorteos} sorteo ganado')
            else:
                estadisticas.append(f'{sorteos} sorteos ganados')
        
        # Agregar información de timbas solo si > 0
        if timbas > 0:
            if timbas == 1:
                estadisticas.append(f'{timbas} timba')
            else:
                estadisticas.append(f'{timbas} timbas')
        
        # Agregar información de margaritas solo si > 0
        if margaritas > 0:
            if margaritas == 1:
                estadisticas.append(f'{margaritas} margarita')
            else:
                estadisticas.append(f'{margaritas} margaritas')
        
        # Agregar récord de escupitajo solo si > 0
        if escupitajo_record > 0:
            estadisticas.append(f'récord de escupitajo: {escupitajo_record} cm')
        
        # Construir mensaje completo
        if len(estadisticas) == 0:
            # Solo puntitos, sin victorias
            mensaje_completo = f'{mensaje_puntitos}!'
        elif len(estadisticas) == 1:
            # Puntitos y una estadística
            mensaje_completo = f'{mensaje_puntitos} y {estadisticas[0]}!'
        else:
            # Puntitos y múltiples estadísticas
            # Unir todas menos la última con comas, y la última con "y"
            estadisticas_texto = ', '.join(estadisticas[:-1]) + ' y ' + estadisticas[-1]
            mensaje_completo = f'{mensaje_puntitos}, {estadisticas_texto}!'
        
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

    @commands.command(aliases=())
    async def random(self, ctx: commands.Context):
        """
        Sorteo aleatorio de 3 puntitos entre usuarios activos
        
        Selecciona un usuario al azar de los que han usado comandos durante
        la sesión (excluyendo admins) y le otorga 3 puntitos. Solo se puede
        usar una vez por sesión del bot.
        
        Args:
            ctx: Contexto del comando de Twitch
            
        Returns:
            None
            
        Requirements:
            - Mínimo 3 usuarios activos (sin contar admins)
            - Solo se puede usar una vez por sesión
            - Los admins no participan del sorteo
            
        Example:
            !random -> "¡@usuario123 ganó 3 puntitos en el sorteo random!"
            !random (segunda vez) -> "El comando !random ya fue usado en esta sesión!"
            !random (pocos usuarios) -> "Se necesitan al menos 3 usuarios activos (sin contar admins). Usuarios activos: 2"
        """
        if await self.check_coma_etilico():
            return
        
        # Verificar si el comando ya fue usado
        if hasattr(self.bot.state, 'random_usado') and self.bot.state.random_usado:
            await mensaje("El comando !random ya fue usado en esta sesión!")
            return
        
        # Obtener usuarios activos excluyendo admins
        usuarios_elegibles = [
            usuario for usuario in self.bot.state.usuarios_activos 
            if usuario.lower() not in [admin.lower() for admin in admins]
        ]
        
        # Verificar que haya al menos 3 usuarios elegibles
        if len(usuarios_elegibles) < 3:
            await mensaje(f"Se necesitan al menos 3 usuarios activos (sin contar admins). Usuarios activos: {len(usuarios_elegibles)}")
            return
        
        # Seleccionar ganador aleatorio
        ganador = choice(usuarios_elegibles)
        
        # Otorgar 3 puntitos
        funcion_puntitos(ganador, 3)
        
        # Marcar comando como usado
        self.bot.state.random_usado = True
        
        # Anunciar ganador
        await mensaje(f"¡@{ganador} ganó 3 puntitos en el sorteo random! 🎉")
