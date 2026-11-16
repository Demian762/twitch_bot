"""
Comandos de avisos: !avisar (cualquiera), !avisos y !cancelaraviso (solo admins)

!avisar <pedido> agenda un aviso para cualquier momento. Claude (Haiku) interpreta el
pedido con salida estructurada: cuándo (relativo o fecha/hora), sobre qué, si el que pide
también lo recibe, y redacta el aviso con la personalidad del bot. Las cuentas de fecha y
hora las hace este código, no el modelo. Los destinatarios salen de las @menciones del
pedido (más el autor si corresponde): el modelo no puede inventar usuarios.

El aviso se guarda en la tabla `recordatorios` de D1 y lo entrega utils/recordatorios.py.

Ejemplos:
    !avisar decime que cambie de juego dentro de 30 minutos
    !avisar avisale a @ejemplo que a las 16 se vaya a estudiar
    !avisar avisame a mí y a @otro el viernes a las 20 que arranca el torneo

Author: Demian762
"""

import asyncio
import json
import re
from datetime import datetime, timedelta

from twitchio.ext import commands

from utils.claude_prompts import PROMPT_AVISO
from utils.configuracion import admins, claude_config
from utils.d1_client import borrar_recordatorio, crear_recordatorio, get_recordatorios
from utils.logger import logger
from utils.mensaje import es_kick, mensaje
from utils.recordatorios import FORMATO_FECHA, ahora_argentina, menciones
from .base_command import BaseCommand


_DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_RE_MENCION = re.compile(r"@(\w+)")

_SCHEMA_AVISO = {
    "type": "object",
    "properties": {
        "entendido": {"type": "boolean"},
        "error": {"type": "string"},
        "tipo": {"type": "string", "enum": ["relativo", "absoluto"]},
        "dias": {"type": "integer"},
        "horas": {"type": "integer"},
        "minutos": {"type": "integer"},
        "segundos": {"type": "integer"},
        "fecha": {"type": "string", "description": "AAAA-MM-DD, hora argentina"},
        "hora": {"type": "string", "description": "HH:MM (24 horas), hora argentina"},
        "incluye_creador": {"type": "boolean"},
        "es_generico": {"type": "boolean"},
        "titulo": {"type": "string"},
        "mensaje": {"type": "string"},
    },
    "required": [
        "entendido", "error", "tipo", "dias", "horas", "minutos", "segundos",
        "fecha", "hora", "incluye_creador", "es_generico", "titulo", "mensaje",
    ],
    "additionalProperties": False,
}


class AvisoInvalido(Exception):
    """El pedido no se pudo convertir en un aviso; el mensaje va tal cual al chat."""


def _bloque_ahora(ahora: datetime) -> str:
    """Fecha actual y calendario de las próximas dos semanas, para que el modelo
    no tenga que calcular a qué fecha cae 'el viernes'."""
    lineas = [
        f"[AHORA] {_DIAS[ahora.weekday()]} {ahora:%Y-%m-%d %H:%M} (hora argentina)",
        "Calendario:",
    ]
    for i in range(15):
        dia = ahora + timedelta(days=i)
        etiqueta = "hoy" if i == 0 else "mañana" if i == 1 else _DIAS[dia.weekday()]
        lineas.append(f"  {etiqueta}: {dia:%Y-%m-%d}")
    return "\n".join(lineas)


def _calcular_vence(datos: dict, ahora: datetime) -> datetime:
    if datos["tipo"] == "relativo":
        partes = [datos["dias"], datos["horas"], datos["minutos"], datos["segundos"]]
        if any(p < 0 for p in partes) or not any(partes):
            raise AvisoInvalido("no entendí dentro de cuánto avisar, probá con algo como 'dentro de 30 minutos'.")
        return ahora + timedelta(
            days=datos["dias"], hours=datos["horas"], minutes=datos["minutos"], seconds=datos["segundos"]
        )

    try:
        vence = datetime.strptime(f"{datos['fecha']} {datos['hora']}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise AvisoInvalido("no entendí para cuándo es el aviso, probá con algo como 'a las 16' o 'mañana a las 9'.")
    if vence <= ahora:
        raise AvisoInvalido(f"el {vence:%d/%m} a las {vence:%H:%M} ya pasó, pedime una hora que todavía no llegó.")
    return vence


def _destinatarios(texto: str, creador: str, incluye_creador: bool) -> list[str]:
    mencionados = []
    for nombre in _RE_MENCION.findall(texto):
        nombre = nombre.lower()
        if nombre not in mencionados:
            mencionados.append(nombre)
    if not mencionados:
        return [creador]
    if incluye_creador:
        return [creador] + [m for m in mencionados if m != creador]
    return mencionados


def _texto_cuando(vence: datetime, ahora: datetime) -> str:
    dias = (vence.date() - ahora.date()).days
    hora = f"a las {vence:%H:%M}"
    if dias == 0:
        cuando = f"hoy {hora}"
    elif dias == 1:
        cuando = f"mañana {hora}"
    elif dias < 7:
        cuando = f"el {_DIAS[vence.weekday()]} {vence:%d/%m} {hora}"
    else:
        cuando = f"el {vence:%d/%m/%Y} {hora}"

    falta = vence - ahora
    if falta < timedelta(hours=24):
        segundos = int(falta.total_seconds())
        h, resto = divmod(segundos, 3600)
        m, s = divmod(resto, 60)
        if h:
            en = f"{h} h {m} min" if m else f"{h} h"
        elif m:
            en = f"{m} min"
        else:
            en = f"{s} s"
        cuando += f" (en {en})"
    return cuando


def _texto_quien(dest: list[str], creador: str) -> str:
    otros = [d for d in dest if d != creador]
    if not otros:
        return "te aviso"
    if len(dest) == len(otros):
        return f"{'le' if len(otros) == 1 else 'les'} aviso a {menciones(otros)}"
    return f"les aviso a vos y a {menciones(otros)}"


class AvisoCommands(BaseCommand):

    async def _interpretar(self, claude_cog, creador: str, pedido: str, ahora: datetime) -> dict:
        prompt = PROMPT_AVISO
        if es_kick():
            prompt = prompt.replace("bot oficial de Twitch", "bot oficial de Kick")
        response = await claude_cog.client.messages.create(
            model=claude_config["modelo_aviso"],
            max_tokens=1000,
            # Haiku 5.5 piensa por defecto y el razonamiento se come max_tokens; acá no
            # hace falta porque el calendario ya viene resuelto en el bloque [AHORA]
            thinking={"type": "disabled"},
            system=[
                {"type": "text", "text": prompt},
                {"type": "text", "text": _bloque_ahora(ahora)},
            ],
            messages=[{"role": "user", "content": f"[PEDIDO DE {creador}] {pedido}"}],
            output_config={"format": {"type": "json_schema", "schema": _SCHEMA_AVISO}},
        )
        logger.info(
            f"Avisar - {creador}: {response.usage.input_tokens} in / {response.usage.output_tokens} out "
            f"({claude_config['modelo_aviso']})"
        )
        if response.stop_reason != "end_turn":
            raise ValueError(f"respuesta incompleta (stop_reason={response.stop_reason})")
        texto = next((b.text for b in response.content if b.type == "text"), "")
        return json.loads(texto)

    @commands.command()
    async def avisar(self, ctx: commands.Context):
        """Agenda un aviso: !avisar avisale a @alguien que X a las 16 / dentro de 30 minutos"""
        creador = ctx.author.name.lower()
        partes = ctx.message.text.split(maxsplit=1)
        if len(partes) < 2 or not partes[1].strip():
            await mensaje(
                f"@{creador} decime cuándo y sobre qué, ej: !avisar decime que cambie de juego dentro de 30 minutos"
            )
            return
        pedido = partes[1].strip()

        coma_msg = self.bot.coma_etilico()
        if coma_msg is not False:
            await mensaje(f"@{creador} {coma_msg}")
            return

        claude_cog = self.bot.my_cogs.get("ClaudioCommands")
        if claude_cog is None:
            logger.error("Avisar - ClaudioCommands no está cargado")
            return

        ahora = ahora_argentina()
        try:
            datos = await self._interpretar(claude_cog, creador, pedido, ahora)
        except Exception as e:
            # Mismo criterio que !claudio y !horoscobot: la causa real queda en el log
            logger.error(f"Avisar - Error en API para {creador}: {type(e).__name__}: {e}")
            await mensaje(f"@{creador} Se acabó la guita de la API, compren cafecitos!")
            return

        try:
            if not datos["entendido"]:
                raise AvisoInvalido(datos["error"] or "no entendí cuándo avisar.")
            vence = _calcular_vence(datos, ahora)
        except AvisoInvalido as e:
            await mensaje(f"@{creador} {e}")
            return

        texto_aviso = datos["mensaje"].strip()
        titulo = datos["titulo"].strip() or "Aviso"
        if datos["es_generico"] and "aviso genérico" not in texto_aviso.lower():
            texto_aviso = f"Aviso genérico: {texto_aviso}" if texto_aviso else "Este es tu aviso genérico."
        if not texto_aviso:
            texto_aviso = "Este es tu aviso genérico."

        dest = _destinatarios(pedido, creador, datos["incluye_creador"])
        fila = {
            "creador": creador,
            "destinatarios": ",".join(dest),
            "titulo": titulo,
            "mensaje": texto_aviso,
            "vence": vence.strftime(FORMATO_FECHA),
            "creado": ahora.strftime(FORMATO_FECHA),
            "pedido": pedido,
        }
        try:
            fila["id"] = await asyncio.to_thread(crear_recordatorio, fila)
        except Exception as e:
            logger.error(f"Avisar - No se pudo guardar el aviso de {creador} en D1: {e}")
            await mensaje(f"@{creador} no pude agendar el aviso, probá de nuevo en un rato.")
            return

        self.bot.recordatorios.agregar(fila)
        logger.info(f"Avisar - Aviso #{fila['id']} de {creador} para {fila['destinatarios']} el {fila['vence']}")
        await mensaje(
            f"@{creador} agendado ⏰ #{fila['id']}: {_texto_cuando(vence, ahora)} "
            f"{_texto_quien(dest, creador)}: {texto_aviso}"
        )

    @commands.command()
    async def avisos(self, ctx: commands.Context):
        """Lista los avisos pendientes (solo admins)"""
        if ctx.author.name.lower() not in admins:
            return
        try:
            filas = await asyncio.to_thread(get_recordatorios)
        except Exception as e:
            logger.error(f"Avisos - No se pudieron leer de D1: {e}")
            await mensaje("No pude leer los avisos, probá de nuevo en un rato.")
            return
        if not filas:
            await mensaje("No hay avisos pendientes.")
            return
        lineas = []
        for f in filas:
            vence = datetime.strptime(f["vence"], FORMATO_FECHA)
            # Sin @ para no arrobar a nadie solo por listar
            para = ", ".join(d for d in f["destinatarios"].split(",") if d)
            lineas.append(f"#{f['id']} · para {para} · {vence:%d/%m/%Y %H:%M} · {f['titulo']}")
        await mensaje(lineas)

    @commands.command()
    async def cancelaraviso(self, ctx: commands.Context):
        """Borra un aviso pendiente por su número: !cancelaraviso 12 (solo admins)"""
        username = ctx.author.name.lower()
        if username not in admins:
            return
        partes = ctx.message.text.split()
        id_texto = partes[1].lstrip("#") if len(partes) > 1 else ""
        if not id_texto.isdigit():
            await mensaje(f"@{username} usá: !cancelaraviso <número> (los números salen en !avisos)")
            return
        id_recordatorio = int(id_texto)
        try:
            borrado = await asyncio.to_thread(borrar_recordatorio, id_recordatorio)
        except Exception as e:
            logger.error(f"Cancelaraviso - No se pudo borrar #{id_recordatorio} de D1: {e}")
            await mensaje(f"@{username} no pude cancelar el aviso, probá de nuevo en un rato.")
            return
        self.bot.recordatorios.quitar(id_recordatorio)
        if borrado:
            logger.info(f"Cancelaraviso - {username} canceló el aviso #{id_recordatorio}")
            await mensaje(f"@{username} aviso #{id_recordatorio} cancelado.")
        else:
            await mensaje(f"@{username} no hay ningún aviso #{id_recordatorio}.")
