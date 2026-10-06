"""
Comando !horoscobot — Horóscopo inventado por Claude (Sonnet) para cada usuario

Características:
    - Una predicción por usuario por sesión del bot (admins incluidos)
    - Cuesta puntitos a los no-admins (claude_config["costo_horoscopo"])
    - No consume el cupo de tokens de !bot ni toca su historial/memoria
    - Un solo tema al azar por predicción: su suerte en puntitos/minijuegos, lo que
      dijo en el chat, el stream/programación o la vida cotidiana en Argentina.
      De fondo siempre: fecha, memoria del usuario (para el trato) y nivel de grog

Author: Demian762
"""

import asyncio
import datetime
import random
from twitchio.ext import commands

from utils.mensaje import mensaje, es_kick
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
_VICTORIAS = [
    ("sorteos_ganados", "sorteos"),
    ("torneos_ganados", "torneos"),
    ("timbas_ganadas", "timbas"),
    ("margaritas_ganadas", "margaritas"),
    ("jackpots_ganados", "jackpots en el slot"),
]


def _cantidad(n: int) -> str:
    if n == 1:
        return "ganó una vez"
    if n <= 4:
        return "ganó varias veces"
    return "ganó un montón de veces"


def _franja_ranking(posicion: int, total: int) -> str:
    if posicion <= 3:
        return "está en el podio del ranking, de los que más tienen"
    if posicion <= max(total * 0.25, 10):
        return "anda por arriba en el ranking"
    if posicion <= total * 0.75:
        return "anda por la mitad de la tabla"
    return "está de los últimos del ranking, casi sin puntitos"


class HoroscoboCommands(BaseCommand):

    # Cada predicción recibe UN solo tema elegido al azar (más los datos de fondo: fecha,
    # memoria, horóscopos previos). Con todo el contexto junto el modelo mezclaba tres
    # referencias por predicción y no se entendía nada.

    def _fecha(self) -> str:
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3)))
        return f"[HOY] {_DIAS[now.weekday()]} {now.day} de {_MESES[now.month - 1]} de {now.year} (Argentina)"

    def _mensajes_propios(self, username: str) -> list[str]:
        return [
            e["msg"] for e in self.bot.state.chat_log
            if e["user"].lower() == username and not e["msg"].startswith("!")
        ][-8:]

    async def _tema_stream(self) -> str:
        lineas = ["el stream y el canal"]
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
        return "\n".join(lineas)

    def _tema_chat(self, username: str) -> str:
        lineas = [f"algo que dijo {username} en el chat (elegí UNO de estos mensajes)"]
        lineas += [f"- {m}" for m in self._mensajes_propios(username)]
        return "\n".join(lineas)

    async def _tema_suerte(self, username: str) -> str:
        # Todo en palabras, sin cifras: con números a la vista el modelo los recita en vez de inventar
        lineas = [f"la suerte de {username} con los puntitos y los minijuegos (elegí UN aspecto)"]
        ranking = await asyncio.to_thread(posicion_ranking, username)
        if ranking:
            lineas.append(f"Puntitos: {_franja_ranking(ranking['posicion_actual'], ranking['total_jugadores'])}.")
            if ranking["historico"] > 0 and ranking["puntos"] < ranking["historico"] * 0.25:
                lineas.append("Ganó bastantes puntitos a lo largo del tiempo pero se le fueron casi todos.")
            v = await asyncio.to_thread(consulta_victorias, username)
            logros = [
                f"{_cantidad(v[campo])} {nombre}"
                for campo, nombre in _VICTORIAS
                if v[campo] > 0
            ]
            if v["escupitajo_record"] > 0:
                logros.append("tiene marca registrada en la competencia de escupitajos")
            lineas.append(
                "Logros: " + "; ".join(logros) + "." if logros else "Nunca ganó nada en los minijuegos."
            )
        else:
            lineas.append("No tiene puntitos registrados todavía (es nuevo o nunca jugó).")
        return "\n".join(lineas)

    async def _tema(self, username: str) -> tuple[str, str]:
        """Elige un tema al azar entre los disponibles y devuelve (nombre, bloque de contexto)."""
        temas = ["suerte", "stream", "argentina"]
        if self._mensajes_propios(username):
            temas.append("chat")
        tema = random.choice(temas)

        if tema == "suerte":
            texto = await self._tema_suerte(username)
        elif tema == "stream":
            texto = await self._tema_stream()
        elif tema == "chat":
            texto = self._tema_chat(username)
        else:
            texto = (
                "la vida cotidiana en Argentina\n"
                "Elegí vos UNA situación cotidiana (el colectivo, el dólar, el asado, el fútbol, "
                "el clima, los trámites, el súper, etc.) y hacé la predicción sobre eso."
            )
        return tema, f"[TEMA DE ESTA PREDICCIÓN] {texto}"

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
            try:
                puntos = await asyncio.to_thread(consulta_puntitos, username)
            except Exception as e:
                logger.error(f"Horoscobot - No se pudieron consultar los puntitos de {username}: {e}")
                state.horoscopo_usados.discard(username)
                await mensaje(f"@{username} los astros no encuentran tus puntitos, probá de nuevo en un rato.")
                return
            if puntos < costo:
                state.horoscopo_usados.discard(username)
                await mensaje(f"@{username} necesitás {costo} puntitos para consultar a los astros.")
                return
            # funcion_puntitos no lanza: si D1 falla devuelve (False, error) y no se cobró nada
            cobrado, _ = await asyncio.to_thread(funcion_puntitos, username, -costo)
            if not cobrado:
                state.horoscopo_usados.discard(username)
                await mensaje(f"@{username} no pude cobrarte los puntitos, probá de nuevo en un rato.")
                return
            cobro_aplicado = True

        try:
            memoria = await claude_cog._cargar_memoria(username)
            prompt = PROMPT_HOROSCOPO
            if es_kick():
                prompt = prompt.replace("bot oficial de Twitch", "bot oficial de Kick")
            tema, bloque_tema = await self._tema(username)
            bloques = [
                {"type": "text", "text": prompt},
                {"type": "text", "text": self._fecha()},
                {"type": "text", "text": bloque_tema},
            ]
            if memoria:
                bloques.append({
                    "type": "text",
                    "text": f"{SECCION_MEMORIA_USUARIO} (solo para saber cómo tratarlo, NO es el tema)\n{memoria}",
                })
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
            # Red de último recurso, a propósito: atrapa cualquier falla de este bloque
            # (sin saldo en la API, red, 529, memoria en D1, respuesta vacía) y en el chat
            # siempre muestra el chiste de "no hay guita". La causa real queda en el log
            # con el tipo de excepción; las fallas previsibles se manejan antes de llegar acá.
            logger.error(f"Horoscobot - Error en API para {username}: {type(e).__name__}: {e}")
            state.horoscopo_usados.discard(username)
            if cobro_aplicado:
                devuelto, _ = await asyncio.to_thread(funcion_puntitos, username, costo)
                if not devuelto:
                    logger.error(f"Horoscobot - No se pudieron devolver {costo} puntitos a {username}")
            await mensaje(f"@{username} Se acabó la guita de la API, compren cafecitos!")
            return

        logger.info(
            f"Horoscobot - {username}{'[admin]' if es_admin else ''} (tema: {tema}): "
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
