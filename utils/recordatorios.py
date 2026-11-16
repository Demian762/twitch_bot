"""
Gestor de avisos de !avisar (recordatorios guardados en la tabla `recordatorios` de D1).

Ciclo de vida de un aviso:
  1. !avisar lo guarda en D1 y lo suma acá con agregar().
  2. Al llegar la hora, si el bot está encendido, se manda al chat:
       - si algún destinatario está activo, se da por entregado y se borra de D1;
       - si ninguno está activo, queda "en espera" (sigue en D1).
  3. Los avisos en espera, y los que vencieron con el bot apagado, se mandan con el
     molde de "aviso perdido" la próxima vez que escribe en el chat alguno de sus
     destinatarios. Ahí se borran de D1.

Un destinatario está activo si está en state.usuarios_activos (usó algún comando en la
sesión) o si escribió cualquier mensaje en el chat en los últimos 10 minutos.

Todas las fechas son hora argentina (UTC-3 fijo, sin horario de verano) y se manejan
como datetime "naive" en esa hora.

Author: Demian762
"""

import asyncio
import time
from datetime import datetime, timedelta, timezone

from utils.d1_client import borrar_recordatorio, get_recordatorios
from utils.logger import logger
from utils.mensaje import mensaje

TZ_ARGENTINA = timezone(timedelta(hours=-3))
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"

_VENTANA_ACTIVO = 10 * 60      # segundos desde el último mensaje para considerar activo a alguien
_INTERVALO_LOOP = 5            # cada cuánto se revisan los avisos que vencen
_REINTENTO_CARGA = 60          # si D1 no responde al arrancar, cada cuánto se reintenta
_MAX_CHARS = 490               # límite de Twitch (500) con margen


def ahora_argentina() -> datetime:
    """Fecha y hora actual en Argentina, sin tzinfo."""
    return datetime.now(TZ_ARGENTINA).replace(tzinfo=None, microsecond=0)


def menciones(usuarios: list[str]) -> str:
    """'@a', '@a y @b', '@a, @b y @c'."""
    arrobados = [f"@{u}" for u in usuarios]
    if len(arrobados) <= 1:
        return "".join(arrobados)
    return ", ".join(arrobados[:-1]) + " y " + arrobados[-1]


def _recortar(texto: str) -> str:
    return texto if len(texto) <= _MAX_CHARS else texto[:_MAX_CHARS - 1] + "…"


def _de_parte(rec: dict) -> str:
    return "" if rec["creador"] in rec["dest"] else f" (de parte de {rec['creador']})"


class RecordatoriosManager:
    """Avisos pendientes de la sesión. Una instancia por bot (Twitch o Kick)."""

    def __init__(self, state) -> None:
        self.state = state
        self._a_tiempo: dict[int, dict] = {}      # vencen con el bot encendido
        self._en_espera: dict[int, dict] = {}     # esperan a que aparezca un destinatario
        self._ultimo_mensaje: dict[str, float] = {}
        self._cargado = False
        self._inicio_sesion: datetime | None = None
        self._task: asyncio.Task | None = None

    # ── Arranque ─────────────────────────────────────────────────────────────

    def iniciar(self) -> None:
        """Arranca el loop de entregas. Idempotente: se puede llamar más de una vez."""
        if self._task is None:
            self._inicio_sesion = ahora_argentina()
            self._task = asyncio.create_task(self._loop())

    async def _cargar_desde_d1(self) -> None:
        try:
            filas = await asyncio.to_thread(get_recordatorios)
        except Exception as e:
            logger.error(f"Recordatorios - No se pudieron cargar desde D1 (se reintenta): {e}")
            return
        for fila in filas:
            if fila["id"] in self._a_tiempo or fila["id"] in self._en_espera:
                continue  # agendado en esta sesión antes de que terminara la carga
            rec = self._desde_fila(fila)
            # Los que vencieron con el bot apagado esperan a su destinatario
            if rec["vence_dt"] <= self._inicio_sesion:
                self._en_espera[rec["id"]] = rec
            else:
                self._a_tiempo[rec["id"]] = rec
        self._cargado = True
        logger.info(
            f"Recordatorios - {len(filas)} cargados desde D1 "
            f"({len(self._en_espera)} vencidos esperando destinatario)"
        )

    @staticmethod
    def _desde_fila(fila: dict) -> dict:
        rec = dict(fila)
        rec["vence_dt"] = datetime.strptime(fila["vence"], FORMATO_FECHA)
        rec["dest"] = [d for d in fila["destinatarios"].split(",") if d]
        return rec

    # ── API para los comandos ────────────────────────────────────────────────

    def agregar(self, fila: dict) -> None:
        """Suma un aviso recién guardado en D1 (fila con su id)."""
        rec = self._desde_fila(fila)
        self._a_tiempo[rec["id"]] = rec

    def quitar(self, id_recordatorio: int) -> None:
        """Saca un aviso de memoria (lo cancelaron con !cancelaraviso)."""
        self._a_tiempo.pop(id_recordatorio, None)
        self._en_espera.pop(id_recordatorio, None)

    # ── Actividad del chat ───────────────────────────────────────────────────

    def registrar_mensaje(self, username: str) -> None:
        """Llamar con cada mensaje del chat (no los del propio bot)."""
        self._ultimo_mensaje[username] = time.monotonic()
        pendientes = [rec for rec in self._en_espera.values() if username in rec["dest"]]
        for rec in pendientes:
            # Se saca de la espera antes de cualquier await para que dos mensajes
            # seguidos del mismo usuario no lo manden dos veces
            del self._en_espera[rec["id"]]
            asyncio.create_task(self._entregar_perdido(rec))

    def _activo(self, username: str) -> bool:
        if username in self.state.usuarios_activos:
            return True
        ultimo = self._ultimo_mensaje.get(username)
        return ultimo is not None and time.monotonic() - ultimo <= _VENTANA_ACTIVO

    # ── Entregas ─────────────────────────────────────────────────────────────

    async def _loop(self) -> None:
        while True:
            try:
                if not self._cargado:
                    await self._cargar_desde_d1()
                ahora = ahora_argentina()
                vencidos = [rec for rec in self._a_tiempo.values() if rec["vence_dt"] <= ahora]
                for rec in vencidos:
                    del self._a_tiempo[rec["id"]]
                    await self._entregar_a_tiempo(rec)
            except Exception as e:
                logger.error(f"Recordatorios - Error en el loop: {e}", exc_info=e)
            await asyncio.sleep(_INTERVALO_LOOP if self._cargado else _REINTENTO_CARGA)

    async def _entregar_a_tiempo(self, rec: dict) -> None:
        alguno_activo = any(self._activo(d) for d in rec["dest"])
        try:
            await mensaje(_recortar(f"{menciones(rec['dest'])} ⏰ {rec['mensaje']}{_de_parte(rec)}"))
        except Exception as e:
            logger.error(f"Recordatorios - No se pudo mandar el aviso #{rec['id']}: {e}")
            self._en_espera[rec["id"]] = rec
            return

        if alguno_activo:
            await self._borrar(rec)
            logger.info(f"Recordatorios - Aviso #{rec['id']} entregado a tiempo a {rec['destinatarios']}")
        else:
            self._en_espera[rec["id"]] = rec
            logger.info(
                f"Recordatorios - Aviso #{rec['id']} mandado pero sin destinatarios activos: "
                f"queda en espera ({rec['destinatarios']})"
            )

    async def _entregar_perdido(self, rec: dict) -> None:
        cuando = rec["vence_dt"].strftime("%d/%m/%Y a las %H:%M")
        texto = (
            f"⏰ Aviso perdido del {cuando} para {menciones(rec['dest'])}: "
            f"{rec['mensaje']}{_de_parte(rec)}"
        )
        try:
            await mensaje(_recortar(texto))
        except Exception as e:
            logger.error(f"Recordatorios - No se pudo mandar el aviso perdido #{rec['id']}: {e}")
            self._en_espera[rec["id"]] = rec
            return
        await self._borrar(rec)
        logger.info(f"Recordatorios - Aviso perdido #{rec['id']} entregado a {rec['destinatarios']}")

    async def _borrar(self, rec: dict) -> None:
        # Se borra después de mandar: si D1 falla, el peor caso es que el aviso se
        # repita la próxima sesión, nunca que se pierda sin entregarse
        try:
            await asyncio.to_thread(borrar_recordatorio, rec["id"])
        except Exception as e:
            logger.error(f"Recordatorios - Aviso #{rec['id']} entregado pero no se pudo borrar de D1: {e}")
