"""
Módulo de inicialización del sistema de comandos del BotDelEstadio

Este módulo centraliza la importación y configuración de todos los cogs
(Command Groups) del bot, facilitando la carga modular de funcionalidades.

El sistema utiliza una lista COGS que contiene todas las clases de comandos
que deben ser cargadas al inicializar el bot. Esto permite un control
centralizado de qué funcionalidades están activas.

Cogs disponibles:
    - BasicCommands: Comandos básicos como !hola, !guardar
    - GameCommands: Información de videojuegos
    - PointsCommands: Sistema de puntitos y consultas
    - MinigamesCommands: Minijuegos y entretenimiento
    - InteractionCommands: Comandos de audio e interacción
    - InsultsCommands: Sistema de pelea de insultos
    - TriviaCommands: Sistema de trivia
    - DrinkCommands: Sistema de grog y embriaguez
    - YoutubeCommands: Videos y podcasts del canal
    - UtilityCommands: Utilidades varias
    - InfoCommands: Información del canal
    - ExtraPointsCommands: Comandos de administración de puntitos

Usage:
    from commands import COGS
    for cog in COGS:
        bot.add_cog(cog(bot))

Author: Demian762
Version: 250927
"""

from .basic_commands import BasicCommands
from .games_commands import GameCommands
from .points_commands import PointsCommands
from .drink_commands import DrinkCommands
from .youtube_commands import YoutubeCommands
from .utility_commands import UtilityCommands
from .minigames_commands import MinigamesCommands
from .info_commands import InfoCommands
from .trivia_commands import TriviaCommands
from .insults_commands import InsultsCommands
from .extra_points_commands import ExtraPointsCommands
from .interaction_commands import InteractionCommands
from .timba_commands import TimbaCommand

# Lista maestra de todos los cogs a cargar
# Esta lista determina qué funcionalidades están activas en el bot
COGS = [
    BasicCommands,
    GameCommands,
    PointsCommands,
    DrinkCommands,
    YoutubeCommands,
    UtilityCommands,
    MinigamesCommands,
    InfoCommands,
    TriviaCommands,
    InsultsCommands,
    ExtraPointsCommands,
    InteractionCommands,
    TimbaCommand
]
