"""
Comandos de administración de puntitos para admins del BotDelEstadio

Este módulo contiene comandos especiales que solo pueden ser ejecutados por
administradores para gestionar el sistema de puntitos, realizar sorteos,
mostrar rankings y dar la bienvenida a nuevos usuarios.

Commands:
    !bienvenida/!bienvenido [usuario] - Otorga 5 puntitos de bienvenida
    !puntito [usuario] - Otorga 1 puntito a un usuario específico  
    !top [n] - Muestra el ranking de usuarios con más puntitos
    !sorteo - Realiza sorteo ponderado entre todos los usuarios y resetea ganador
    !sorteopresentes - Realiza sorteo ponderado solo entre usuarios activos (excluyendo admins)

Permissions: Solo usuarios en la lista de admins pueden ejecutar estos comandos

Author: Demian762
Version: 250927
"""

import asyncio
from twitchio.ext import commands
from random import randint
from utils.logger import logger
from utils.mensaje import mensaje
from utils.puntitos_manager import funcion_puntitos, top_puntitos, sorteo_puntitos, sorteo_puntitos_presentes, registrar_victoria_sorteo
from utils.configuracion import admins
from .base_command import BaseCommand

class ExtraPointsCommands(BaseCommand):
    """
    Cog que maneja comandos de administración del sistema de puntitos
    
    Estos comandos están restringidos únicamente a usuarios administradores
    y permiten gestionar el sistema de puntitos de manera directa.
    """
    
    @commands.command(aliases="bienvenido")
    async def bienvenida(self, ctx: commands.Context, nombre: str):
        """
        Otorga puntitos de bienvenida a un usuario (solo admins)
        
        Comando especial para dar la bienvenida a nuevos usuarios del stream
        otorgando 5 puntitos automáticamente. Si un usuario no autorizado
        intenta usarlo, pierde 1 puntito como penalización.
        
        Args:
            ctx (commands.Context): Contexto del comando
            nombre (str): Nombre del usuario que recibirá los puntitos
            
        Permissions:
            Solo usuarios en la lista de admins pueden ejecutar este comando
            
        Example:
            Admin: !bienvenida NuevoUsuario
            Bot: @NuevoUsuario acaba de sumar cinco puntitos de bienvenida!
            
            Usuario: !bienvenida OtroUsuario  
            Bot: @Usuario acaba de perder un puntito por usar comandos de admin!
        """
        if await self.check_coma_etilico():
            return
            
        if ctx.author.name in admins:
            funcion_puntitos(nombre, 5)
            await mensaje(f'@{nombre.lstrip("@")} acaba de sumar cinco puntitos de bienvenida!')
        else:
            funcion_puntitos(nombre, -1)
            await mensaje(f'@{nombre.lstrip("@")} acaba de perder un puntito por hacerse el vivo!')

    @commands.command()
    async def puntito(self, ctx: commands.Context, nombre: str):
        if await self.check_coma_etilico():
            return
            
        if ctx.author.name in admins:
            funcion_puntitos(nombre)
            await mensaje(f'@{nombre.lstrip("@")} acaba de sumar un puntito!')
        else:
            funcion_puntitos(nombre, -1)
            await mensaje(f'@{nombre.lstrip("@")} acaba de perder un puntito por hacerse el vivo!')

    @commands.command()
    async def top(self, ctx: commands.Context, n=3):
        if await self.check_coma_etilico():
            return
            
        nombre = ctx.author.name
        if nombre in admins:
            lista = [f"El top {n} de puntitos es:"]
            top = top_puntitos(n)
            lista.extend(top)
            await mensaje(lista)

    @commands.command()
    async def sorteo(self, ctx: commands.Context):
        """Sorteo ponderado entre todos los usuarios del spreadsheet"""
        if await self.check_coma_etilico():
            return
            
        autor = ctx.author.name
        if autor in admins:
            ganador = sorteo_puntitos()
            
            # Verificar si hubo error o no hay participantes elegibles
            if ganador in ["Error en sorteo", "No hay participantes", "No hay participantes elegibles"]:
                await mensaje(ganador)
                return
            
            texto = ["¡SORTEO INICIADO!","sorteando...."]
            await mensaje(texto)
            await asyncio.sleep(randint(1,30))
            texto = ["AND THE WINNER IS:", ganador]
            await mensaje(texto)
            # Registrar la victoria del sorteo en el spreadsheet
            registrar_victoria_sorteo(ganador)

    @commands.command()
    async def sorteopresentes(self, ctx: commands.Context):
        """Sorteo ponderado solo entre usuarios activos (presentes en el chat, excluyendo admins)"""
        if await self.check_coma_etilico():
            return
            
        autor = ctx.author.name
        if autor in admins:
            # Obtener usuarios activos del bot
            usuarios_activos = self.bot.state.usuarios_activos
            
            if not usuarios_activos:
                await mensaje("No hay usuarios activos para el sorteo")
                return
            
            ganador = sorteo_puntitos_presentes(usuarios_activos, admins)
            
            # Verificar si hubo error o no hay participantes elegibles
            if ganador in ["Error en sorteo", "No hay participantes", "No hay participantes elegibles"]:
                await mensaje(ganador)
                return
            
            texto = ["¡SORTEO DE PRESENTES INICIADO!","sorteando...."]
            await mensaje(texto)
            await asyncio.sleep(randint(1,30))
            texto = ["AND THE WINNER IS:", ganador]
            await mensaje(texto)
            # Registrar la victoria del sorteo en el spreadsheet (misma columna que !sorteo)
            registrar_victoria_sorteo(ganador)
