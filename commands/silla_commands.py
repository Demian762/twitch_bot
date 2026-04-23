"""
Comando !silla — reproduce audios al azar de forma continua

Solo disponible para admins. Cada uso alterna entre activar y detener el loop.
Entre audio y audio se espera 1 segundo.

Author: Demian762
"""

import asyncio
import winsound
from random import choice

from twitchio.ext import commands

from utils.logger import logger
from utils.mensaje import mensaje
from utils.utiles_general import resource_path, play_sound
from utils.configuracion import admins
from .base_command import BaseCommand

AUDIOS_SILLA = [
    "alert", "allahu", "arrugadito", "bija", "boca", "cuervo", "dark",
    "dificil", "distinta", "dross", "elisir", "elpollodiablo", "emilio",
    "emperor", "ernesto", "fumojuego", "gatito", "helldiver", "holis",
    "margarita_1", "margarita_2", "margarita_3", "mario", "milk", "nodenuevo",
    "piripipi", "play", "presta", "quiereme", "repartidor", "sacrilegioso",
    "sadsong", "saran", "sega", "snake", "tose", "wansaia82", "win95",
    "win98", "yamete", "yeahbaby", "zazaraza", "zelda",
]

class SillaCommands(BaseCommand):
    def __init__(self, bot):
        super().__init__(bot)
        self._silla_task: asyncio.Task | None = None

    @commands.command()
    async def silla(self, ctx: commands.Context):
        if ctx.author.name.lower() not in admins:
            return

        if self._silla_task and not self._silla_task.done():
            self._silla_task.cancel()
            self._silla_task = None
            await mensaje("La silla frenó. PogChamp")
        else:
            await mensaje("La silla empieza a girar... PogChamp")
            self._silla_task = asyncio.create_task(self._loop_silla())

    async def _loop_silla(self):
        loop = asyncio.get_running_loop()
        try:
            while True:
                audio = choice(AUDIOS_SILLA)
                audio_path = resource_path(f"storage/{audio}.wav")
                await loop.run_in_executor(
                    None,
                    lambda p=audio_path: play_sound(p, winsound.SND_FILENAME | winsound.SND_NODEFAULT),
                )
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error en loop de !silla: {e}")
