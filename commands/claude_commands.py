"""
Comandos !claudio / !bot — Interacción con Claude AI personalizado como el Bot del Estadio

Características:
    - Personalidad argenta del Bot del Estadio
    - Contexto del canal cargado desde Google Sheets (programación, top puntitos)
    - Memoria a largo plazo por usuario: guardada en la hoja "Claude" del Sheet
    - Tool use: RAWG.io y Steam para info de videojuegos en tiempo real
    - Costo: 1 puntito por uso (bloqueado con 0 o negativos)
    - Límite de tokens por usuario por sesión (configurable en configuracion.py)
    - Historial de conversación por usuario en la sesión actual

Author: Demian762
"""

import asyncio
from twitchio.ext import commands
import anthropic

from utils.mensaje import mensaje
from utils.audios import comandos_audios
from utils.puntitos_manager import (
    consulta_puntitos,
    funcion_puntitos,
    get_memoria_claude,
    guardar_memoria_claude,
    top_puntitos,
)
from utils.api_games import steam_price
from utils.configuracion import claude_config, admins
from utils.secretos import anthropic_api_key
from utils.logger import logger
from utils.claude_prompts import (
    PROMPT_BASE,
    PROMPT_ADMIN,
    PROMPTS_ADMINS,
    PROMPT_MEMORIA,
    SECCION_DATOS_CANAL,
    SECCION_MEMORIA_USUARIO,
)
from .base_command import BaseCommand


TOOLS = [
    {
        "name": "buscar_juego_rawg",
        "description": (
            "Busca información de un videojuego específico en RAWG.io: "
            "nombre oficial, fecha de lanzamiento, plataformas y puntaje Metacritic. "
            "Usar para cualquier pregunta sobre un juego concreto."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre_juego": {
                    "type": "string",
                    "description": "Nombre del juego a buscar"
                }
            },
            "required": ["nombre_juego"]
        }
    },
    {
        "name": "proximos_lanzamientos",
        "description": (
            "Obtiene los próximos lanzamientos de videojuegos "
            "en un rango de 15 días atrás a 30 días adelante."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limite": {
                    "type": "integer",
                    "description": "Cantidad de juegos a listar (máximo 5)",
                    "default": 5
                }
            },
            "required": []
        }
    },
    {
        "name": "buscar_precio_steam",
        "description": "Busca el precio en pesos argentinos de un juego en Steam.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre_juego": {
                    "type": "string",
                    "description": "Nombre del juego a buscar en Steam"
                }
            },
            "required": ["nombre_juego"]
        }
    },
    {
        "name": "actualizar_contexto_canal",
        "description": (
            "Actualiza el snapshot del canal: recarga el top de puntitos actual y la programación semanal. "
            "Usar cuando el usuario pregunte sobre el ranking actual de puntitos o cuando los datos del canal "
            "puedan estar desactualizados en la sesión."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "buscar_info_usuario",
        "description": (
            "Busca lo que el bot recuerda sobre otro usuario del canal. "
            "Usar cuando alguien pregunte por otra persona del chat (ej: '¿qué onda con pepito?', '¿conocés a fulano?'). "
            "No usar para buscar info del propio usuario que está hablando."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "Nombre de usuario de Twitch a buscar (sin @)"
                }
            },
            "required": ["username"]
        },
        "cache_control": {"type": "ephemeral"}
    }
]


class ClaudioCommands(BaseCommand):

    def __init__(self, bot):
        super().__init__(bot)
        self.client = anthropic.AsyncAnthropic(api_key=anthropic_api_key)

    def _build_system_prompt(self, username: str, memoria_usuario: str, es_admin: bool) -> list:
        if username in PROMPTS_ADMINS:
            base = PROMPTS_ADMINS[username]
        elif es_admin:
            base = PROMPT_ADMIN
        else:
            base = PROMPT_BASE
        ctx = self.bot.state.claude_contexto
        bloques = [{"type": "text", "text": base}]
        if ctx:
            # cache_control aquí marca el fin del prefijo cacheable:
            # cubre el prompt base + todos los datos del canal (la parte más grande y estable)
            bloques.append({
                "type": "text",
                "text": f"{SECCION_DATOS_CANAL}\n{ctx}",
                "cache_control": {"type": "ephemeral"}
            })
        if memoria_usuario:
            # sin cache_control: es única por usuario, cachearla solo desperdiciaría slots
            bloques.append({
                "type": "text",
                "text": f"{SECCION_MEMORIA_USUARIO}\n{memoria_usuario}"
            })
        return bloques

    def _build_info_comandos(self) -> str:
        """Genera un texto con todos los comandos del bot a partir de los cogs cargados."""
        lines = ["COMANDOS DISPONIBLES EN EL BOT:"]
        seen = set()

        for cog_name, cog in self.bot.my_cogs.items():
            cog_lines = []
            for cmd_name, cmd in cog.__all_commands__.items():
                # Saltar entradas de alias (aparecen repetidas en el dict)
                if cmd_name != cmd.name:
                    continue
                if cmd.name in seen:
                    continue
                seen.add(cmd.name)
                # El comando interactuar es el dispatcher interno de audios — se lista aparte
                if cmd.name == "interactuar":
                    continue

                doc = ""
                if hasattr(cmd, "callback") and cmd.callback.__doc__:
                    for line in cmd.callback.__doc__.strip().splitlines():
                        line = line.strip()
                        if line:
                            doc = line
                            break

                aliases_str = ""
                if cmd.aliases:
                    aliases_str = " (también: !" + " !".join(cmd.aliases) + ")"

                entry = f"  !{cmd.name}{aliases_str}"
                if doc:
                    entry += f" — {doc}"
                cog_lines.append(entry)

            if cog_lines:
                section = cog_name.replace("Commands", "").replace("Command", "")
                lines.append(f"\n[{section}]")
                lines.extend(cog_lines)

        lines.append("\n[Sonidos / efectos de audio]")
        for audio, aliases in comandos_audios.items():
            aliases_str = " | ".join(f"!{a}" for a in aliases)
            lines.append(f"  {aliases_str} — reproduce el audio '{audio}'")

        return "\n".join(lines)

    def build_contexto_completo_sync(self) -> str:
        """
        Construye el contexto completo del canal para el system prompt de Claude:
        programación semanal, top puntitos y lista completa de comandos.
        Llamado en setup_hook (via asyncio.to_thread) y desde el tool actualizar_contexto_canal.
        """
        programacion = self.bot.config.lista_programacion
        top = top_puntitos(5)

        lineas = ["PROGRAMACIÓN SEMANAL DEL STREAM:"]
        lineas += [f"  - {p}" for p in programacion]
        lineas.append("\nTOP 5 PUNTITOS ACTUALES:")
        lineas += [f"  {i+1}. {n}" for i, n in enumerate(top)]
        lineas.append("")
        lineas.append(self._build_info_comandos())

        return "\n".join(lineas)

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        rawg = self.bot.api.rawg
        steam = self.bot.api.steam
        dolar = self.bot.api.dolar

        if tool_name == "buscar_juego_rawg":
            nombre, puntaje, fecha = rawg.info(tool_input["nombre_juego"])
            if nombre is None:
                return "No se encontró ese juego en la base de datos."
            if nombre is False:
                return "Error al consultar RAWG.io."
            puntaje_str = str(puntaje) if puntaje else "sin Metacritic"
            fecha_str = str(fecha) if fecha else "fecha desconocida"
            return f"Juego: {nombre} | Metacritic: {puntaje_str} | Lanzado: {fecha_str}"

        elif tool_name == "proximos_lanzamientos":
            limite = min(tool_input.get("limite", 5), 5)
            resultados = rawg.lanzamientos(limite)
            if not resultados:
                return "No se encontraron próximos lanzamientos."
            return " | ".join(resultados)

        elif tool_name == "buscar_precio_steam":
            nombre_steam, precio = steam_price(tool_input["nombre_juego"], steam, dolar)
            if not nombre_steam:
                return "No se encontró ese juego en Steam."
            return f"{nombre_steam}: ${precio} ARS"

        elif tool_name == "actualizar_contexto_canal":
            self.bot.state.claude_contexto = self.build_contexto_completo_sync()
            return "Contexto del canal actualizado: programación, ranking de puntitos y lista completa de comandos refrescados."

        elif tool_name == "buscar_info_usuario":
            username_buscar = tool_input["username"].lower().lstrip("@")
            # Intentar desde cache de sesión primero
            memoria = self.bot.state.claude_memoria_cache.get(username_buscar)
            if memoria is None:
                memoria = get_memoria_claude(username_buscar)
                if memoria:
                    self.bot.state.claude_memoria_cache[username_buscar] = memoria
            if not memoria:
                return f"No tengo info guardada sobre '{username_buscar}'."
            return f"Lo que sé sobre {username_buscar}: {memoria}"

        return "Herramienta desconocida."

    async def _call_claude(self, historial: list, system: list) -> tuple[str, int]:
        """Llama a Claude con loop de tool use. Retorna (texto_respuesta, tokens_usados)."""
        max_tokens = claude_config["max_tokens_respuesta"]
        messages = historial.copy()
        total_tokens = 0

        for _ in range(5):  # máximo 5 rondas de tool use para evitar loops infinitos
            response = await self.client.messages.create(
                model=claude_config["modelo"],
                max_tokens=max_tokens,
                system=system,
                tools=TOOLS,
                messages=messages
            )
            cache_creation = getattr(response.usage, "cache_creation_input_tokens", 0) or 0
            cache_read = getattr(response.usage, "cache_read_input_tokens", 0) or 0
            total_tokens += response.usage.input_tokens + response.usage.output_tokens + cache_creation
            if cache_creation or cache_read:
                logger.debug(f"Claudio cache — creación: {cache_creation}, lectura: {cache_read}")

            if response.stop_reason == "end_turn":
                text = next((b.text for b in response.content if hasattr(b, "text")), "")
                return text.strip(), total_tokens

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = await asyncio.to_thread(
                            self._execute_tool, block.name, block.input
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })

                messages.append({"role": "user", "content": tool_results})
            else:
                break

        return "No pude procesar eso.", total_tokens

    async def _actualizar_memoria(self, username: str, historial: list, memoria_anterior: str) -> None:
        """
        Tarea en background: le pide a Claude un resumen actualizado del usuario
        y lo guarda en la hoja Claude del Sheet.
        Corre después de cada interacción, sin bloquear la respuesta al chat.
        """
        try:
            # Construir contexto de la conversación reciente para el resumen
            fragmento = "\n".join(
                f"{'Usuario' if m['role'] == 'user' else 'Bot'}: {m['content'] if isinstance(m['content'], str) else '[tool use]'}"
                for m in historial[-6:]  # últimos 3 intercambios
            )
            prompt_memoria = (
                f"Resumen anterior del usuario '{username}': {memoria_anterior or '(ninguno)'}\n\n"
                f"Conversación reciente:\n{fragmento}\n\n"
                "En base a esto, escribí un resumen actualizado de 1 a 3 oraciones sobre este usuario: "
                "quién es, qué le interesa, cómo interactúa con el bot. Solo el resumen, sin introducciones."
            )
            response = await self.client.messages.create(
                model=claude_config["modelo"],
                max_tokens=150,
                system=PROMPT_MEMORIA,
                messages=[{"role": "user", "content": prompt_memoria}]
            )
            nuevo_resumen = response.content[0].text.strip()
            await asyncio.to_thread(guardar_memoria_claude, username, nuevo_resumen)
            self.bot.state.claude_memoria_cache[username] = nuevo_resumen
        except Exception as e:
            logger.error(f"Claudio memoria - Error al actualizar memoria de {username}: {e}")

    async def _cargar_memoria(self, username: str) -> str:
        """
        Carga la memoria del usuario desde el cache de sesión o, si es la primera vez,
        desde la hoja Claude del Sheet.
        """
        if username in self.bot.state.claude_memoria_cache:
            return self.bot.state.claude_memoria_cache[username]
        memoria = await asyncio.to_thread(get_memoria_claude, username)
        self.bot.state.claude_memoria_cache[username] = memoria
        return memoria

    @commands.command(aliases=("bot",))
    async def claudio(self, ctx: commands.Context):
        username = ctx.author.name.lower()

        # Extraer texto de la pregunta
        partes = ctx.message.text.split(maxsplit=1)
        if len(partes) < 2 or not partes[1].strip():
            await mensaje(f"@{username} ¿qué me querés preguntar? Usá: !claudio <tu pregunta>")
            return

        texto = partes[1].strip()

        es_admin = username in [a.lower() for a in admins]

        # Verificar puntitos (bloqueado con 0 o negativos — admins exentos)
        if not es_admin:
            puntos = await asyncio.to_thread(consulta_puntitos, username)
            if puntos <= 0:
                await mensaje(f"@{username} no tenés puntitos para consultar a Claudio. ¡Ganá algunos primero!")
                return

        # Verificar límite de tokens de sesión (admins exentos)
        tokens_usados = self.bot.state.claude_token_usage.get(username, 0)
        if not es_admin and tokens_usados >= claude_config["max_tokens_por_usuario_sesion"]:
            await mensaje(f"@{username} ya consumiste tu cupo de Claudio por esta sesión. ¡Volvé mañana!")
            return

        # Descontar 1 puntito (admins exentos)
        if not es_admin:
            await asyncio.to_thread(funcion_puntitos, username, -1)

        # Cargar memoria del usuario (Sheet → cache → system prompt)
        memoria_usuario = await self._cargar_memoria(username)

        # Construir historial de sesión
        historial = self.bot.state.claude_historial.get(username, [])
        historial.append({"role": "user", "content": texto})

        try:
            system = self._build_system_prompt(username, memoria_usuario, es_admin)
            respuesta, tokens_nuevos = await self._call_claude(historial, system)
        except Exception as e:
            logger.error(f"Claudio - Error en API para {username}: {e}")
            if not es_admin:
                await asyncio.to_thread(funcion_puntitos, username, 1)
            await mensaje(f"@{username} Claudio está en modo coma etílico, probá de nuevo.")
            return

        # Actualizar estado de sesión
        self.bot.state.claude_token_usage[username] = tokens_usados + tokens_nuevos
        historial.append({"role": "assistant", "content": respuesta})
        max_pares = claude_config["historial_max_pares"]
        self.bot.state.claude_historial[username] = historial[-(max_pares * 2):]

        limite_str = "sin límite" if es_admin else str(claude_config["max_tokens_por_usuario_sesion"])
        logger.info(
            f"Claudio - {username}{'[admin]' if es_admin else ''}: {tokens_nuevos} tokens nuevos "
            f"(sesión: {tokens_usados + tokens_nuevos}/{limite_str})"
        )

        # Enviar respuesta al chat (Twitch: máx 500 chars por mensaje)
        respuesta_completa = f"@{username} {respuesta}"
        if len(respuesta_completa) <= 490:
            await mensaje(respuesta_completa)
        else:
            for chunk in [respuesta_completa[i:i+490] for i in range(0, len(respuesta_completa), 490)][:2]:
                await mensaje(chunk)

        # Actualizar memoria en background (no bloquea la respuesta al chat)
        asyncio.create_task(
            self._actualizar_memoria(username, self.bot.state.claude_historial[username], memoria_usuario)
        )
