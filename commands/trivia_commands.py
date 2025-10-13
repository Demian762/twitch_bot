"""
Comandos de trivia interactiva

Este módulo implementa un sistema de trivia donde los usuarios pueden
iniciar preguntas aleatorias o específicas y competir por responder correctamente.

Author: Demian762
Version: 250927
"""

import asyncio
from random import choice, shuffle
from twitchio.ext import commands
from Levenshtein import distance as lev

# Imports locales
from utils.mensaje import mensaje
from utils.utiles_general import get_args
from utils.logger import logger
from utils.configuracion import trivia, trivia_limite
from .base_command import BaseCommand

class TriviaCommands(BaseCommand):
    """
    Cog para sistema de trivia interactiva
    
    Maneja preguntas de trivia con múltiples opciones, incluyendo
    inicialización de preguntas aleatorias o específicas por nombre.
    
    Attributes:
        bot: Instancia del bot principal
        trivia: Diccionario de preguntas y respuestas
        trivia_limite: Límite de similitud para respuestas
    """
    def __init__(self, bot):
        """
        Inicializa el cog de comandos de trivia
        
        Args:
            bot: Instancia del bot principal
        """
        super().__init__(bot)

    @commands.command(aliases=("trivial",))
    async def trivia(self, ctx: commands.Context, *args):
        """
        Comando principal de trivia
        
        Inicia una nueva pregunta de trivia (aleatoria o específica) o
        continúa con una trivia existente evaluando respuestas.
        
        Args:
            ctx: Contexto del comando de Twitch
            *args: Respuesta del usuario o nombre específico de trivia
            
        Returns:
            None
            
        Example:
            !trivia -> Inicia trivia aleatoria
            !trivia historia -> Busca trivia sobre historia
            !trivia [respuesta] -> Responde a trivia activa
        """
        if await self.check_coma_etilico():
            return
        
        respuesta = get_args(args)
        
        if self.bot.state.trivia_actual is None and len(respuesta) == 0:
            self.bot.state.trivia_actual = choice(list(trivia.items()))
            logger.info(f"TRIVIA INICIADA - Pregunta: {self.bot.state.trivia_actual[0]}")
            logger.info(f"RESPUESTA CORRECTA: {self.bot.state.trivia_actual[1][0]}")
            await mensaje(self.bot.state.trivia_actual[0])
            await asyncio.sleep(self.bot.config.basic.get("dont_spam"))
            await mensaje(self.bot.state.trivia_actual[1])
        
        elif self.bot.state.trivia_actual is None and len(respuesta) > 0:
            for k, v in trivia.items():
                if lev(respuesta, k.lower()) <= 10:
                    self.bot.state.trivia_actual = (k,v)
                    break
            
            if self.bot.state.trivia_actual is None:
                await mensaje(f'"{respuesta}" no es una trivia!')
                return
                
            await mensaje(self.bot.state.trivia_actual[0])
            logger.info(f"TRIVIA ESPECÍFICA INICIADA - Pregunta: {self.bot.state.trivia_actual[0]}")
            logger.info(f"RESPUESTA CORRECTA: {self.bot.state.trivia_actual[1][0]}")
            await asyncio.sleep(self.bot.config.basic.get("dont_spam"))
            lista_desordenada = self.bot.state.trivia_actual[1].copy()
            shuffle(lista_desordenada)
            await mensaje(lista_desordenada)
            
        elif self.bot.state.trivia_actual is not None and len(respuesta) == 0:
            await mensaje(f"Te faltó la respuesta {ctx.author.name}!")
            
        elif self.bot.state.trivia_actual is not None and respuesta.lower() == "respuesta":
            respuesta_correcta = self.bot.state.trivia_actual[1][0]
            await mensaje(f'La respuesta correcta es: "{respuesta_correcta}"')
            self.bot.state.trivia_actual = None
            
        elif self.bot.state.trivia_actual is not None and len(respuesta) > 0:
            if lev(respuesta, self.bot.state.trivia_actual[1][0].lower()) < trivia_limite.get(self.bot.state.trivia_actual[0], 3):
                logger.info(f"TRIVIA RESPONDIDA CORRECTAMENTE por {ctx.author.name} - Respuesta: {respuesta}")
                await mensaje(f'Correcto! Bien por {ctx.author.name}!')
                self.bot.state.trivia_actual = None
            else:
                logger.info(f"TRIVIA RESPUESTA INCORRECTA por {ctx.author.name} - Respuesta: {respuesta} | Correcta: {self.bot.state.trivia_actual[1][0]}")
                await mensaje('Nooooo, incorrecto!!')
