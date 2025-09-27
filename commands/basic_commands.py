from twitchio.ext import commands
from utils.logger import logger
from utils.mensaje import mensaje
from utils.puntitos_manager import funcion_puntitos
from utils.configuracion import admins, spam_messenges
from .base_command import BaseCommand

class BasicCommands(BaseCommand):
    def __init__(self, bot):
        super().__init__(bot)
        self.puntitos_dados = []
        self.proteccion_activa = False

    @commands.command(aliases=("buenas",))
    async def hola(self, ctx: commands.Context):
        if await self.check_coma_etilico():
            return
        nombre = ctx.author.name
        await mensaje([f"hola {nombre}!"])
        if nombre not in self.puntitos_dados:
            self.puntitos_dados.append(nombre)
            funcion_puntitos(nombre, 1)
            await mensaje(f'@{nombre.lstrip("@")} acaba de sumar un puntito!')
        else:
            await mensaje(f'Ya tenés tu puntito de hoy @{nombre.lstrip("@")}, no jodas....')

    @commands.command(aliases=("salvar",))
    async def guardar(self, ctx: commands.Context):
        if await self.check_coma_etilico():
            return
        nombre = ctx.author.name
        msj1 = f"{nombre} quiere recordarles que...."
        msj2 = "¡¡¡GUARDEN LA PARTIDA!!!"
        await mensaje([msj1,msj2])

    @commands.command()
    async def proteccion(self, ctx: commands.Context):
        if await self.check_coma_etilico():
            return
        if self.proteccion_activa == False:
            await mensaje("Aqui comienza el horario de proteccion al menor.")
            self.proteccion_activa = True
        else:
            await mensaje("Aqui finaliza el horario de proteccion al menor.")
            self.proteccion_activa = False

    @commands.command()
    async def spam(self, ctx: commands.Context):
        if await self.check_coma_etilico():
            return
        autor = ctx.author.name
        if autor not in admins:
            return
        await mensaje(spam_messenges)
        await mensaje(spam_messenges)
        await mensaje(spam_messenges)
