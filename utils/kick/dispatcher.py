"""
Dispatcher de comandos para Kick.

twitchio resuelve y ejecuta comandos a través de su propio Context, que está
construido a partir de sus modelos internos de Twitch (ChatMessage, Chatter,
PartialUser) — no es algo que se pueda alimentar con datos de otra plataforma.
En vez de pelear con eso, este dispatcher reutiliza directamente las clases
de comandos existentes (COGS) sin pasar por el routing de twitchio:

  1. Instancia cada Component de COGS una sola vez (como setup_hook lo hace
     para Twitch), pasándole el KickBot como `self.bot`.
  2. Junta todos los Command ya decorados con @commands.command (el objeto
     Command.callback es la función real tal cual está escrita en
     commands/*.py, sin ningún cambio) en un registro nombre/alias -> Command.
  3. Ante cada mensaje de chat de Kick, hace su propio parseo de prefijo y
     argumentos (mucho más simple que el de twitchio: acá los comandos solo
     usan tipos básicos — str, int, *args) y llama directo a Command.callback.

Los ~52 comandos de commands/*.py no se tocan: corren igual en Twitch (vía
twitchio) y en Kick (vía este dispatcher).
"""

import inspect

from commands import COGS
from utils.kick.context import KickContext
from utils.logger import logger

PREFIX = "!"


class MissingRequiredArgument(Exception):
    def __init__(self, param_name: str) -> None:
        self.param_name = param_name
        super().__init__(f"falta el argumento requerido '{param_name}'")


class KickCommandDispatcher:
    """Registra los comandos de COGS y despacha mensajes de chat de Kick hacia ellos."""

    def __init__(self, bot) -> None:
        self.bot = bot
        self.components: dict[str, object] = {}
        self._registry: dict[str, tuple[object, object]] = {}
        self._load_components()

    def _load_components(self) -> None:
        for cog_class in COGS:
            component = cog_class(self.bot)
            self.components[cog_class.__name__] = component

            for method_name, cmd in cog_class.__all_commands__.items():
                for name in (method_name, *cmd.aliases):
                    name = name.lower()
                    if name in self._registry:
                        logger.warning(f"[kick_dispatcher] Comando duplicado ignorado: '{name}'")
                        continue
                    self._registry[name] = (component, cmd)

        self.bot.my_cogs = self.components
        logger.info(
            f"[kick_dispatcher] {len(self._registry)} comandos/alias cargados "
            f"de {len(self.components)} components"
        )

    @staticmethod
    def _convert(raw: str, annotation) -> object:
        if annotation is inspect.Parameter.empty or annotation is str:
            return raw
        if annotation is int:
            return int(raw)
        if annotation is float:
            return float(raw)
        if annotation is bool:
            return raw.strip().lower() in ("1", "true", "si", "sí", "yes")
        return raw  # anotaciones no soportadas (no usadas hoy en commands/*.py): se pasan crudas

    def _parse_arguments(self, cmd, rest: str) -> tuple[list, dict]:
        tokens = rest.split() if rest.strip() else []
        args: list = []
        idx = 0

        for name, param in cmd.parameters.items():
            if param.kind == param.VAR_POSITIONAL:
                args.extend(tokens[idx:])
                idx = len(tokens)
                continue

            if param.kind == param.KEYWORD_ONLY:
                if idx < len(tokens):
                    remaining = " ".join(tokens[idx:])
                    args.append(self._convert(remaining, param.annotation))
                    idx = len(tokens)
                elif param.default is param.empty:
                    raise MissingRequiredArgument(name)
                continue

            if idx >= len(tokens):
                if param.default is param.empty:
                    raise MissingRequiredArgument(name)
                args.append(param.default)
                continue

            try:
                args.append(self._convert(tokens[idx], param.annotation))
            except (TypeError, ValueError):
                raise MissingRequiredArgument(name)
            idx += 1

        return args, {}

    async def dispatch(self, username: str, text: str) -> bool:
        """Procesa un mensaje de chat de Kick. Devuelve True si matcheó un comando registrado."""
        if not text.startswith(PREFIX):
            return False

        parts = text[len(PREFIX):].split(maxsplit=1)
        if not parts:
            return False

        name = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ""

        entry = self._registry.get(name)
        if entry is None:
            logger.info(f"El comando '{name}' no existe — Usuario: {username}")
            return False

        component, cmd = entry
        ctx = KickContext(username, text)

        try:
            args, kwargs = self._parse_arguments(cmd, rest)
            await cmd.callback(component, ctx, *args, **kwargs)
            logger.info(f"[kick_dispatcher] Comando '{name}' ejecutado (usuario {username})")
        except MissingRequiredArgument as e:
            logger.info(f"[kick_dispatcher] Comando '{name}' — {e} (usuario {username})")
        except Exception as e:
            logger.error(f"[kick_dispatcher] Error en comando '{name}': {e}", exc_info=e)
            from utils.mensaje import mensaje
            await mensaje("Ya rompiste el bot con ese comando...")

        return True
