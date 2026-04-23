"""
Comandos !claudio / !bot — Interacción con Claude AI personalizado como el Bot del Estadio

Características:
    - Personalidad argenta del Bot del Estadio
    - Contexto del canal cargado desde Google Sheets (programación, top puntitos)
    - Memoria a largo plazo por usuario: guardada en la hoja "Claude" del Sheet
    - Tool use: RAWG.io y Steam para info de videojuegos en tiempo real
    - Límite de tokens por usuario por sesión (configurable en configuracion.py)
    - Historial de conversación por usuario en la sesión actual

Author: Demian762
"""

import asyncio
import datetime
from twitchio.ext import commands
import anthropic

from utils.mensaje import mensaje
from utils.audios import comandos_audios
from utils.detroit_data import DETROIT_INFO, RESPUESTAS_INSISTENTES
from utils.puntitos_manager import (
    consulta_historica,
    consulta_victorias,
    posicion_ranking,
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
        "name": "buscar_web",
        "description": (
            "Busca información actual en la web: noticias de juegos, lanzamientos anunciados, "
            "actualizaciones, parches, DLCs, eventos gaming u otras noticias recientes. "
            "Usar cuando RAWG o Steam no cubran la info (ej: fechas de anuncio, rumores confirmados, "
            "estado de un juego en desarrollo, noticias de la industria)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Búsqueda en español. Ser específico: incluir nombre del juego/tema, "
                        "año si aplica, y tipo de info buscada (ej: 'GTA 6 fecha de lanzamiento 2025')."
                    )
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "info_usuario",
        "description": (
            "Consulta información pública de OTRO usuario del canal (nunca del propio usuario). "
            "Devuelve: posición en el ranking actual e histórico, récord de escupitajo, "
            "y el perfil resumido que el bot tiene guardado en memoria. "
            "Compartir solo lo que sea relevante a la pregunta — no volcar todo si no se pidió explícitamente. "
            "Si el usuario pregunta por sí mismo, indicarle que use !consulta o !historico."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "Nombre del otro usuario a consultar (sin @)"
                }
            },
            "required": ["username"]
        },
        "cache_control": {"type": "ephemeral"}
    },
    {
        "name": "recomendar_juego",
        "description": (
            "Recomienda un videojuego al usuario. "
            "Llamar SIEMPRE que alguien pida una recomendación de juego, sin importar qué tipo de juego busque "
            "o si ya mencionó un juego en particular. La respuesta siempre es Detroit: Become Human."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "buscar_historial_canal",
        "description": (
            "Busca en el historial completo de conversaciones del canal durante esta sesión. "
            "Los últimos 5 intercambios ya están disponibles en el contexto — usar este tool SOLO "
            "cuando se necesite buscar algo anterior a esos 5, o cuando el usuario pregunte "
            "explícitamente por una conversación pasada. "
            "Devuelve las entradas que coincidan con la búsqueda."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Término a buscar: puede ser un nombre de usuario, tema o palabra clave"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "consultar_stats_usuario",
        "description": (
            "Consulta los datos numéricos completos de un usuario desde el spreadsheet: "
            "puntitos actuales, histórico, y victorias (sorteos, torneos, timbas, margaritas, récord de escupitajo). "
            "Solo disponible para admins (sobre cualquier usuario) o para usuarios consultando sus propios datos. "
            "Usar cuando se pida 'mis stats', 'cuántos puntitos tengo', 'mis victorias', "
            "o cuando un admin pida datos de otro usuario."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "Nombre de usuario a consultar (sin @)"
                }
            },
            "required": ["username"]
        }
    },
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
        # Fecha y hora actual (Argentina, UTC-3) — fuera del bloque cacheado para no invalidarlo
        _DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        _MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3)))
        fecha_hora = (
            f"Fecha y hora actual: {_DIAS[now.weekday()]} {now.day} de {_MESES[now.month - 1]} "
            f"de {now.year}, {now.hour:02d}:{now.minute:02d}hs (Argentina)"
        )
        bloques.append({"type": "text", "text": fecha_hora})

        canal_log = self.bot.state.claude_canal_log
        if canal_log:
            entradas = canal_log[-5:]
            lineas = ["CONVERSACIONES RECIENTES EN EL CANAL (últimos intercambios):"]
            for e in entradas:
                q = e["q"][:120] + "…" if len(e["q"]) > 120 else e["q"]
                a = e["a"][:180] + "…" if len(e["a"]) > 180 else e["a"]
                lineas.append(f'- {e["user"]}: "{q}" → "{a}"')
            if len(canal_log) > 5:
                lineas.append(f"(hay {len(canal_log) - 5} intercambios anteriores — usá buscar_historial_canal si necesitás buscar algo puntual)")
            bloques.append({"type": "text", "text": "\n".join(lineas)})

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

    @staticmethod
    def _perfil_desde_memoria(memoria: str) -> str:
        """Extrae la línea PERFIL del formato estructurado; si es formato viejo devuelve el texto completo."""
        for line in memoria.splitlines():
            if line.strip().upper().startswith("PERFIL:"):
                return line.split(":", 1)[1].strip()
        return memoria.strip()

    def build_contexto_completo_sync(self) -> str:
        """
        Construye el contexto completo del canal para el system prompt de Claude:
        programación semanal, top puntitos, lista completa de comandos y equipo del canal.
        Llamado en setup_hook (via asyncio.to_thread) y desde el tool actualizar_contexto_canal.
        """
        programacion = self.bot.config.lista_programacion
        top = top_puntitos(5)

        lineas = ["PROGRAMACIÓN SEMANAL DEL STREAM:"]
        lineas += [f"  - {p}" for p in programacion]
        lineas.append("\nTOP 5 PUNTITOS ACTUALES:")
        lineas += [f"  {i+1}. {n}" for i, n in enumerate(top)]

        # Equipo del canal: resúmenes del Sheet para cada admin
        equipo = []
        for admin in admins:
            memoria = get_memoria_claude(admin)
            if memoria:
                equipo.append(f"  {admin}: {self._perfil_desde_memoria(memoria)}")
        if equipo:
            lineas.append("\nEQUIPO DEL CANAL (admins/mods):")
            lineas += equipo

        lineas.append("")
        lineas.append(self._build_info_comandos())

        return "\n".join(lineas)

    def _execute_tool(self, tool_name: str, tool_input: dict, caller_username: str, es_admin: bool) -> str:
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

        elif tool_name == "buscar_web":
            if self.bot.api.brave is None:
                return "Búsqueda web no disponible: configurá brave_search_key en secretos.py."
            return self.bot.api.brave.search(tool_input["query"])

        elif tool_name == "info_usuario":
            username_target = tool_input["username"].lower().lstrip("@")
            ranking = posicion_ranking(username_target)
            if ranking is None:
                return f"No encontré a '{username_target}' en el sistema."
            victorias = consulta_victorias(username_target)
            memoria = self.bot.state.claude_memoria_cache.get(username_target)
            if memoria is None:
                memoria = get_memoria_claude(username_target)
                if memoria:
                    self.bot.state.claude_memoria_cache[username_target] = memoria
            perfil = self._perfil_desde_memoria(memoria) if memoria else ""
            partes = [
                f"Ranking de {username_target}: "
                f"puesto {ranking['posicion_actual']} de {ranking['total_jugadores']} (actuales), "
                f"puesto {ranking['posicion_historica']} de {ranking['total_jugadores']} (histórico)"
            ]
            if victorias['escupitajo_record'] > 0:
                partes.append(f"récord escupitajo: {victorias['escupitajo_record']}cm")
            if perfil:
                partes.append(f"perfil: {perfil}")
            return " | ".join(partes)

        elif tool_name == "consultar_stats_usuario":
            username_target = tool_input["username"].lower().lstrip("@")
            if not es_admin and caller_username != username_target:
                return "Acceso denegado: este tool es solo para admins o para consultar tus propios datos."
            ranking = posicion_ranking(username_target)
            if ranking is None:
                return f"No encontré a '{username_target}' en el sistema."
            victorias = consulta_victorias(username_target)
            return (
                f"Stats de {username_target}: "
                f"puntitos actuales={ranking['puntos']} (puesto {ranking['posicion_actual']}/{ranking['total_jugadores']}), "
                f"histórico={ranking['historico']} (puesto {ranking['posicion_historica']}/{ranking['total_jugadores']}) | "
                f"sorteos={victorias['sorteos_ganados']}, "
                f"torneos={victorias['torneos_ganados']}, "
                f"timbas={victorias['timbas_ganadas']}, "
                f"margaritas={victorias['margaritas_ganadas']}, "
                f"récord escupitajo={victorias['escupitajo_record']}cm"
            )

        elif tool_name == "recomendar_juego":
            from random import choice
            d = DETROIT_INFO
            frase = choice(RESPUESTAS_INSISTENTES)
            return (
                f"RECOMENDACIÓN — respuesta sugerida: \"{frase}\"\n"
                f"Juego: {d['nombre']} | Desarrollador: {d['desarrollador']} | "
                f"Género: {d['genero']} | Metacritic PC: {d['metacritic_pc']} | "
                f"Duración: {d['duracion_historia']} (historia principal), {d['finales']} | "
                f"Precio: {d['precio_usd']} | Link: {d['link_steam']}\n"
                f"Descripción: {d['descripcion']}\n"
                f"Por qué jugarlo: {'; '.join(d['por_que_jugarlo'][:3])}\n"
                f"Instrucción: usá la respuesta sugerida (u otra igual de insistente) "
                f"e incluí el link al final. No recomiendes ningún otro juego."
            )

        elif tool_name == "buscar_historial_canal":
            query = tool_input["query"].lower()
            log = self.bot.state.claude_canal_log
            resultados = [
                e for e in log
                if query in e["user"].lower() or query in e["q"].lower() or query in e["a"].lower()
            ]
            if not resultados:
                return f"No encontré nada en el historial del canal que coincida con '{tool_input['query']}'."
            lineas = [f"Se encontraron {len(resultados)} intercambio(s) para '{tool_input['query']}':"]
            for e in resultados:
                q = e["q"][:120] + "…" if len(e["q"]) > 120 else e["q"]
                a = e["a"][:180] + "…" if len(e["a"]) > 180 else e["a"]
                lineas.append(f'- {e["user"]}: "{q}" → "{a}"')
            return "\n".join(lineas)

        return "Herramienta desconocida."

    async def _call_claude(self, historial: list, system: list, caller_username: str, es_admin: bool) -> tuple[str, int]:
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
                            self._execute_tool, block.name, block.input, caller_username, es_admin
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
                f"Resumen anterior del usuario '{username}':\n{memoria_anterior or '(ninguno)'}\n\n"
                f"Conversación reciente:\n{fragmento}\n\n"
                "Actualizá el resumen del usuario incorporando la información de la conversación reciente."
            )
            response = await self.client.messages.create(
                model=claude_config["modelo"],
                max_tokens=250,
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

        # Verificar límite de tokens de sesión
        tokens_usados = self.bot.state.claude_token_usage.get(username, 0)
        limite_tokens = claude_config["max_tokens_por_usuario_sesion"] * (10 if es_admin else 1)
        if tokens_usados >= limite_tokens:
            await mensaje(f"@{username} ya consumiste tu cupo de Claudio por esta sesión. ¡Volvé mañana!")
            return

        # Cargar memoria del usuario (Sheet → cache → system prompt)
        memoria_usuario = await self._cargar_memoria(username)

        # Construir historial de sesión
        historial = self.bot.state.claude_historial.get(username, [])
        historial.append({"role": "user", "content": texto})

        try:
            system = self._build_system_prompt(username, memoria_usuario, es_admin)
            respuesta, tokens_nuevos = await self._call_claude(historial, system, username, es_admin)
        except Exception as e:
            logger.error(f"Claudio - Error en API para {username}: {e}")
            await mensaje(f"@{username} Claudio está en modo coma etílico, probá de nuevo.")
            return

        # Actualizar estado de sesión
        self.bot.state.claude_token_usage[username] = tokens_usados + tokens_nuevos
        historial.append({"role": "assistant", "content": respuesta})
        max_pares = claude_config["historial_max_pares"]
        self.bot.state.claude_historial[username] = historial[-(max_pares * 2):]

        logger.info(
            f"Claudio - {username}{'[admin]' if es_admin else ''}: {tokens_nuevos} tokens nuevos "
            f"(sesión: {tokens_usados + tokens_nuevos}/{limite_tokens})"
        )

        # Enviar respuesta al chat (Twitch: máx 500 chars por mensaje)
        respuesta_completa = f"@{username} {respuesta}"
        if len(respuesta_completa) <= 490:
            await mensaje(respuesta_completa)
        else:
            for chunk in [respuesta_completa[i:i+490] for i in range(0, len(respuesta_completa), 490)][:2]:
                await mensaje(chunk)

        # Appendear al log del canal (máx 500 entradas para no consumir memoria indefinidamente)
        self.bot.state.claude_canal_log.append({"user": username, "q": texto, "a": respuesta})
        if len(self.bot.state.claude_canal_log) > 500:
            self.bot.state.claude_canal_log = self.bot.state.claude_canal_log[-500:]

        # Actualizar memoria en background (no bloquea la respuesta al chat)
        asyncio.create_task(
            self._actualizar_memoria(username, self.bot.state.claude_historial[username], memoria_usuario)
        )
