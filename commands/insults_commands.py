"""
Comandos de pelea de insultos interactiva

Este módulo implementa un minijuego de pelea de insultos donde los usuarios
pueden retar al bot a un duelo verbal usando algoritmos de distancia de Levenshtein
para evaluar la precisión de las respuestas.

Author: Demian762
Version: 250927
"""

from twitchio.ext import commands
from random import choice
from Levenshtein import distance as lev
from utils.utiles_general import get_args
from utils.mensaje import mensaje
from utils.puntitos_manager import funcion_puntitos
from utils.configuracion import insultos_dict, respuestas_dict

from .base_command import BaseCommand

class InsultsCommands(BaseCommand):
    """
    Cog para minijuego de pelea de insultos
    
    Implementa un sistema de duelo verbal donde los usuarios deben responder
    correctamente a insultos del bot. Usa algoritmos de similitud de cadenas
    para evaluar respuestas.
    
    Attributes:
        bot: Instancia del bot principal
        peleas: Diccionario que rastrea peleas activas por usuario
        insultos_dict: Diccionario de insultos disponibles
        respuestas_dict: Diccionario de respuestas correctas
    """
    def __init__(self, bot):
        """
        Inicializa el cog de comandos de insultos
        
        Args:
            bot: Instancia del bot principal
        """
        super().__init__(bot)
        self.peleas = {}

    @commands.command(aliases=("insulto", "pelea", "peleainsultos", "peleadeinsulto", "peleainsulto", "peleadeinsultos",))
    async def insultos(self, ctx: commands.Context, *args):
        """
        Comando principal de pelea de insultos
        
        Inicia o continúa una pelea de insultos entre el usuario y el bot.
        El objetivo es ganar 3 rondas respondiendo correctamente a los insultos.
        
        Args:
            ctx: Contexto del comando de Twitch
            *args: Respuesta del usuario al insulto
            
        Returns:
            None
            
        Example:
            !insultos -> Inicia nueva pelea
            !insultos [respuesta] -> Responde al insulto actual
        """
        if await self.check_coma_etilico():
            return
            
        nombre = ctx.author.name.lower()
        respuesta = get_args(args)
        enviar = []

        if not self.peleas.get(nombre):
            self.peleas[nombre] = {"hist":[], "score": [0, 0]}
            enviar.append(f"{nombre} retó al BOT a una pelea de insultos! Debe ganarle tres veces!")

        if self.peleas[nombre]["score"][0] >= 3:
            await mensaje("La pelea terminó! Ya me ganaste!")
            return
        if self.peleas[nombre]["score"][1] >= 3:
            await mensaje("La pelea terminó! Fuiste derrotado!")
            return

        if self.peleas[nombre]["hist"] == []:
            key = choice(list(insultos_dict.keys()))
            self.peleas[nombre]["hist"].append(key)
            enviar.append(insultos_dict.get(key))
        
        else:
            key = self.peleas[nombre]["hist"][-1]
            num = lev(respuestas_dict.get(key),respuesta)

            if num <= self.bot.config.basic.get("limite"):
                enviar.append(f"Ouch! Punto para {ctx.author.name}")
                score = self.peleas[nombre]["score"][0] + 1
                self.peleas[nombre]["score"][0] = score

                if self.peleas[nombre]["score"][0] >= 3:
                    enviar.append(f"{nombre} ganó la pelea de insultos!")
                    funcion_puntitos(nombre, cant=5)
                    enviar.append(f'{nombre} acaba de sumar cinco puntitos!')
                    await mensaje(enviar)
                    return

            else:
                enviar.append("Ajaaa!! Punto para el BOT")
                score = self.peleas[nombre]["score"][1] + 1
                self.peleas[nombre]["score"][1] = score

                if self.peleas[nombre]["score"][1] >= 3:
                    enviar.append(f"{nombre} perdió la pelea de insultos!")
                    await mensaje(enviar)
                    return
            
            while True:
                key = choice(list(insultos_dict.keys()))
                if key not in self.peleas[nombre]["hist"]:
                    break
            self.peleas[nombre]["hist"].append(key)
            enviar.append(insultos_dict.get(key))

        await mensaje(enviar)
