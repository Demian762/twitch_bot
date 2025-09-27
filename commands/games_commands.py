"""
Comandos relacionados con videojuegos e información gaming

Este módulo maneja comandos que proporcionan información sobre videojuegos,
integrando múltiples APIs para ofrecer datos completos sobre títulos,
precios, scores y próximos lanzamientos.

Commands:
    !info [juego] - Información completa de un videojuego
    !lanzamientos [limite] - Próximos lanzamientos de videojuegos

APIs integradas:
    - RAWG API: Base de datos de videojuegos y scores
    - Steam API: Precios de videojuegos
    - HowLongToBeat API: Tiempos de juego
    - DolarAPI: Conversión de precios a pesos argentinos

Author: Demian762
Version: 250927
"""

from twitchio.ext import commands

# Imports locales
from utils.mensaje import mensaje
from utils.utiles_general import get_args
from utils.api_games import howlong, steam_price
from utils.logger import logger
from utils.configuracion import admins
from .base_command import BaseCommand

class GameCommands(BaseCommand):
    """
    Cog que maneja comandos de información de videojuegos
    
    Integra múltiples APIs para proporcionar información completa sobre
    videojuegos incluyendo scores, precios, tiempos de juego y lanzamientos.
    """
    
    @commands.command()
    async def info(self, ctx: commands.Context, *args):
        """
        Proporciona información completa sobre un videojuego
        
        Busca un videojuego en múltiples bases de datos y APIs para mostrar:
        - Nombre oficial del juego
        - Puntuación de Metacritic
        - Fecha de lanzamiento
        - Tiempo promedio de juego (HowLongToBeat)
        - Precio en Steam (convertido a pesos argentinos)
        
        Args:
            ctx (commands.Context): Contexto del comando
            *args: Palabras que forman el nombre del juego a buscar
            
        Example:
            Usuario: !info The Witcher 3
            Bot: The Witcher 3: Wild Hunt // 93 puntos en Metacritic // 2015-05-19 // ⏱️ 51.5 Hours Main Story // 💰 $1,299 ARS
            
        Note:
            - Si no se encuentra el juego, muestra mensaje de error
            - Maneja errores de APIs individuales sin fallar completamente
            - Utiliza wrapper interno _info() para manejo de errores
        """
        if await self.check_coma_etilico():
            return
            
        handler = await self.handle_command(self._info)
        await handler(ctx, *args)

    async def _info(self, ctx: commands.Context, *args):
        """
        Implementación interna del comando info con manejo detallado de APIs
        
        Proceso de búsqueda:
        1. Busca el juego en RAWG API (nombre, score, fecha)
        2. Obtiene tiempo de juego de HowLongToBeat
        3. Busca precio en Steam API
        4. Convierte precio usando cotización del dólar
        5. Formatea y envía respuesta completa
        
        Args:
            ctx (commands.Context): Contexto del comando  
            *args: Argumentos del nombre del juego
        """
        juego = get_args(args)
        nombre, puntaje, fecha = self.bot.api.rawg.info(juego)
        if nombre == 200:
            await mensaje("La base de datos no está funcionando bien, intentá en un toque!")
            return
        if nombre is None:
            await mensaje("No se encontró nada en la base de datos!")
            return
        try:
            tiempo = howlong(juego)
        except:
            tiempo = None
        nombre_steam, precio = steam_price(nombre, self.bot.api.steam, self.bot.api.dolar)
        sep = " // "
        output = nombre
        if puntaje:
            output = output + sep + str(puntaje) + " puntos en Metacritic"
        if fecha:
            output = output + sep + fecha
        if tiempo:
            output = output + sep + tiempo + " horas"
        if nombre_steam:
            output = output + sep + str(precio) + " pesos en Steam."
        output = output + "."
        await mensaje(output)

    @commands.command()
    async def lanzamientos(self, ctx: commands.Context, limite = 3):
        if await self.check_coma_etilico():
            return
            
        handler = await self.handle_command(self._lanzamientos) 
        await handler(ctx, limite)

    async def _lanzamientos(self, ctx: commands.Context, limite):
        if ctx.author.name not in admins and limite > 3:
            limite = 3
        output = self.bot.api.rawg.lanzamientos(limite)
        if output is not False:
            await mensaje(output)
        else:
            await mensaje("No encontré lanzamientos.")
