import asyncio
from twitchio.ext import commands
from random import randint
from utils.logger import logger
from utils.mensaje import mensaje
from utils.puntitos_manager import funcion_puntitos, top_puntitos, sorteo_puntitos
from utils.configuracion import admins
from .base_command import BaseCommand

class ExtraPointsCommands(BaseCommand):
    @commands.command(aliases="bienvenido")
    async def bienvenida(self, ctx: commands.Context, nombre: str):
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
        if await self.check_coma_etilico():
            return
            
        autor = ctx.author.name
        if autor in admins:
            ganador = sorteo_puntitos()
            texto = ["¡SORTEO INICIADO!","sorteando...."]
            await mensaje(texto)
            await asyncio.sleep(randint(1,30))
            texto = ["AND THE WINNER IS:", ganador]
            await mensaje(texto)
