"""
Comando !horoscobot — Horóscopo inventado por Claude (Sonnet) para cada usuario

Características:
    - Una predicción por usuario por sesión del bot (admins incluidos)
    - Cuesta puntitos a los no-admins (claude_config["costo_horoscopo"])
    - No consume el cupo de tokens de !bot ni toca su historial/memoria
    - Contexto: memoria del usuario, puntitos/victorias, su chat reciente,
      título/categoría del stream, programación y nivel de grog

Author: Demian762
"""

import asyncio
import datetime
from twitchio.ext import commands

from utils.mensaje import mensaje
from utils.puntitos_manager import (
    consulta_puntitos,
    consulta_victorias,
    funcion_puntitos,
    posicion_ranking,
)
from utils.configuracion import claude_config, admins
from utils.logger import logger
from utils.claude_prompts import PROMPT_HOROSCOPO, SECCION_MEMORIA_USUARIO
from .base_command import BaseCommand


_DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
          "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


class HoroscoboCommands(BaseCommand):

    async def _contexto_stream(self) -> str:
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3)))
        lineas = [
            "[STREAM ACTUAL]",
            f"Fecha y hora: {_DIAS[now.weekday()]} {now.day} de {_MESES[now.month - 1]} "
            f"de {now.year}, {now.hour:02d}:{now.minute:02d}hs (Argentina)",
        ]
        try:
            channel = await self.bot.fetch_channel(self.bot.broadcaster_id)
            if channel:
                if channel.title:
                    lineas.append(f"Título del stream: {channel.title}")
                game_name = getattr(channel, "game_name", "")
                if game_name:
                    lineas.append(f"Categoría/juego: {game_name}")
        except Exception as e:
            logger.warning(f"Horoscobot - No se pudo obtener info del canal: {e}")

        programacion = self.bot.config.lista_programacion
        if programacion:
            lineas.append("Programación semanal:")
            lineas += [f"  - {p}" for p in programacion]
        lineas.append(f"Grogs que tomó el bot en la sesión: {self.bot.state.grog_count}")
        return "\n".join(lineas)

    def _contexto_chat(self, username: str) -> str | None:
        chat_log = self.bot.state.chat_log
        if not chat_log:
            return None

        entradas = []
        acumulado = 0
        for e in reversed(chat_log):
            costo = len(e["user"]) + len(e["msg"]) + 4
            if acumulado + costo > 1500:
                break
            entradas.append(e)
            acumulado += costo

        lineas = ["[CHAT RECIENTE DEL CANAL]"]
        lineas += [f'- {e["user"]}: {e["msg"]}' for e in reversed(entradas)]

        propios = [e["msg"] for e in chat_log if e["user"].lower() == username][-8:]
        if propios:
            lineas.append(f"\n[ÚLTIMOS MENSAJES DE {username}]")
            lineas += [f"- {m}" for m in propios]
        return "\n".join(lineas)

    async def _contexto_usuario(self, username: str, memoria: str) -> str:
        lineas = [f"[USUARIO: {username}]"]
        ranking = await asyncio.to_thread(posicion_ranking, username)
        if ranking:
            lineas.append(
                f"Puntitos: {ranking['puntos']} (puesto {ranking['posicion_actual']} de {ranking['total_jugadores']}), "
                f"histórico: {ranking['historico']} (puesto {ranking['posicion_historica']})"
            )
            v = await asyncio.to_thread(consulta_victorias, username)
            lineas.append(
                f"Victorias: sorteos={v['sorteos_ganados']}, torneos={v['torneos_ganados']}, "
                f"timbas={v['timbas_ganadas']}, margaritas={v['margaritas_ganadas']}, "
                f"jackpots={v['jackpots_ganados']}, récord escupitajo={v['escupitajo_record']}cm"
            )
        else:
            lineas.append("No tiene puntitos registrados todavía (es nuevo o nunca jugó).")
        if memoria:
            lineas.append(f"\n{SECCION_MEMORIA_USUARIO}\n{memoria}")
        return "\n".join(lineas)

    def _contexto_horoscopos_previos(self) -> str | None:
        previos = self.bot.state.horoscopos
        if not previos:
            return None
        lineas = ["[HORÓSCOPOS YA DADOS EN ESTA SESIÓN]"]
        lineas += [f"- {u}: {t}" for u, t in list(previos.items())[-10:]]
        return "\n".join(lineas)

    @commands.command()
    async def horoscobot(self, ctx: commands.Context):
        """Te tira el horóscopo (1 por sesión, cuesta puntitos)"""
        username = ctx.author.name.lower()
        es_admin = username in admins
        state = self.bot.state
        costo = claude_config["costo_horoscopo"]

        if username in state.horoscopo_usados:
            await mensaje(f"@{username} los astros ya hablaron por hoy, volvé la próxima sesión.")
            return

        coma_msg = self.bot.coma_etilico()
        if coma_msg is not False:
            await mensaje(f"@{username} {coma_msg}")
            return

        claude_cog = self.bot.my_cogs.get("ClaudioCommands")
        if claude_cog is None:
            logger.error("Horoscobot - ClaudioCommands no está cargado")
            return

        # Se marca antes de cualquier await para que un doble envío no cobre ni llame dos veces
        state.horoscopo_usados.add(username)

        cobro_aplicado = False
        if not es_admin:
            puntos = await asyncio.to_thread(consulta_puntitos, username)
            if puntos < costo:
                state.horoscopo_usados.discard(username)
                await mensaje(f"@{username} necesitás {costo} puntitos para consultar a los astros.")
                return
            await asyncio.to_thread(funcion_puntitos, username, -costo)
            cobro_aplicado = True

        try:
            memoria = await claude_cog._cargar_memoria(username)
            bloques = [
                {"type": "text", "text": PROMPT_HOROSCOPO},
                {"type": "text", "text": await self._contexto_stream()},
            ]
            chat = self._contexto_chat(username)
            if chat:
                bloques.append({"type": "text", "text": chat})
            bloques.append({"type": "text", "text": await self._contexto_usuario(username, memoria)})
            previos = self._contexto_horoscopos_previos()
            if previos:
                bloques.append({"type": "text", "text": previos})
            bloques.append({"type": "text", "text": claude_cog._ebriedad_prompt(state.grog_count)})

            # Sonnet 5.5 piensa por defecto y el razonamiento se come max_tokens antes de
            # escribir el texto; "between_tools" lo apaga (sin tools, no piensa nunca)
            response = await claude_cog.client.messages.create(
                model=claude_config["modelo_horoscopo"],
                max_tokens=1000,
                thinking={"type": "between_tools"},
                system=bloques,
                messages=[{"role": "user", "content": f"Tirale el horóscopo a {username}."}],
            )
            texto = next((b.text for b in response.content if b.type == "text"), "").strip()
            if not texto:
                raise ValueError(f"respuesta vacía (stop_reason={response.stop_reason})")
        except Exception as e:
            logger.error(f"Horoscobot - Error en API para {username}: {e}")
            state.horoscopo_usados.discard(username)
            if cobro_aplicado:
                await asyncio.to_thread(funcion_puntitos, username, costo)
            await mensaje(f"@{username} Se acabó la guita de la API, compren cafecitos!")
            return

        logger.info(
            f"Horoscobot - {username}{'[admin]' if es_admin else ''}: "
            f"{response.usage.input_tokens} in / {response.usage.output_tokens} out ({claude_config['modelo_horoscopo']})"
        )

        sufijo = f" (-{costo} puntitos)" if cobro_aplicado else ""
        respuesta_completa = f"@{username} 🔮 {texto}{sufijo}"
        if len(respuesta_completa) <= 490:
            await mensaje(respuesta_completa)
        else:
            for chunk in [respuesta_completa[i:i+490] for i in range(0, len(respuesta_completa), 490)][:2]:
                await mensaje(chunk)

        state.horoscopos[username] = texto
        state.claude_canal_log.append({"user": username, "q": "!horoscobot", "a": texto})
        if len(state.claude_canal_log) > 500:
            state.claude_canal_log = state.claude_canal_log[-500:]
