"""
Comandos de interacción con audios y efectos de sonido

Este módulo maneja comandos que reproducen efectos de audio y ejecutan
rutinas periódicas del bot, incluyendo sistema de regalías para audios exclusivos.

Author: Demian762
Version: 250927
"""

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
    """
    Cog para comandos de interacción con audios y rutinas
    
    Maneja la reproducción de efectos de sonido, mensajes asociados y
    un sistema de regalías para comandos de audio exclusivos de ciertos usuarios.
    
    Attributes:
        bot: Instancia del bot principal
        rutinas: Rutina periódica del bot
        comandos_audios: Mapeo de comandos a archivos de audio
        autores_exclusivos: Sistema de regalías por uso de audios exclusivos
    """
    def __init__(self, bot):
        """
        Inicializa el cog de comandos de interacción
        
        Args:
            bot: Instancia del bot principal
        """
        super().__init__(bot)
        self.rutinas.start()
        
    @commands.command(aliases=(comandos_general))
    async def interactuar(self, ctx: commands.Context):
        """
        Comando dinámico para reproducción de audios interactivos
        
        Detecta el comando usado, reproduce el audio asociado y maneja
        el sistema de regalías para audios exclusivos.
        
        Args:
            ctx: Contexto del comando de Twitch
            
        Returns:
            None
            
        Note:
            Este comando tiene alias dinámicos basados en comandos_general
        """
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
        """
        Rutina periódica para mostrar mensajes automáticos
        
        Ejecuta mensajes programados según el cronograma configurado,
        rotando entre diferentes mensajes informativos.
        
        Returns:
            None
            
        Note:
            Se ejecuta cada 'rutina_timer' minutos según configuración
        """
        actual = self.bot.state.rutinas_counter["actual"]
        mensaje_actual = self.bot.rutina_lista[actual]

        await mensaje([mensaje_actual])

        if actual >= self.bot.state.rutinas_counter["total"]:
            self.bot.state.rutinas_counter["actual"] = 0
        else:
            self.bot.state.rutinas_counter["actual"] = actual + 1
