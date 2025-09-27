from twitchio.ext import commands, routines
import winsound

# Imports locales
from utils.logger import logger
from utils.mensaje import mensaje
from utils.utiles_general import resource_path
from utils.puntitos_manager import funcion_puntitos
from utils.configuracion import admins, configuracion_basica
from utils.audios import comandos_general, comandos_audios, comandos_mensajes, autores_exclusivos
from .base_command import BaseCommand

class InteractionCommands(BaseCommand):
    def __init__(self, bot):
        super().__init__(bot)
        self.rutinas.start()
        
    @commands.command(aliases=(comandos_general))
    async def interactuar(self, ctx: commands.Context):
        if await self.check_coma_etilico():
            return
            
        autor = ctx.author.name
        comando = (str(ctx.message.content).lstrip("!").split(' ')[0]).lower()
        comando_validado = None

        for llave, valores in comandos_audios.items():
            if comando in valores:
                comando_validado = llave
                break

        if comando_validado:
            audio_path = resource_path(f"storage\{comando_validado}.wav")
            winsound.PlaySound(audio_path,winsound.SND_FILENAME)
            mensaje_string = comandos_mensajes.get(comando_validado, None)
        else:
            mensaje_string = comandos_mensajes.get(comando, None)

        await mensaje(mensaje_string)

        if autor in admins:
            return

        for llave, valores in autores_exclusivos.items():
            if comando_validado in valores and autor != llave:
                funcion_puntitos(autor, -1)
                funcion_puntitos(llave, 1)
                await mensaje(f"@{autor} acaba de pagarle 1 puntito a @{llave} en concepto de regalías.")

    @routines.routine(minutes=configuracion_basica["rutina_timer"], wait_first=True)
    async def rutinas(self):
        actual = self.bot.rutinas_counter["actual"]
        mensaje_actual = self.bot.rutina_lista[actual]

        await mensaje([mensaje_actual])

        if actual >= self.bot.rutinas_counter["total"]:
            self.bot.rutinas_counter["actual"] = 0
        else:
            self.bot.rutinas_counter["actual"] = actual + 1
