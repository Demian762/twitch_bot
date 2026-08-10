"""
KickContext — objeto liviano que imita la porción de twitchio.ext.commands.Context
que efectivamente usan los comandos existentes (commands/*.py): .author.name,
.message.text y .send(). No hereda de twitchio ni depende de él; es un
duck-type independiente, así los mismos comandos corren sin cambios tanto
sobre Twitch (con el Context real de twitchio) como sobre Kick (con este).
"""

from dataclasses import dataclass

from utils.mensaje import mensaje


@dataclass
class _Author:
    name: str


@dataclass
class _Message:
    text: str


class KickContext:
    """Contexto mínimo pasado a los comandos cuando corren sobre Kick."""

    def __init__(self, username: str, text: str) -> None:
        self.author = _Author(name=username)
        self.message = _Message(text=text)

    async def send(self, content: str) -> None:
        await mensaje(content)
