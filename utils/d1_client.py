"""
Cliente HTTP del Worker de Cloudflare que expone la base D1 de puntitos.

Reemplaza el acceso directo a Google Sheets (gspread) de utils/puntitos_manager.py.
Sigue el mismo estilo síncrono + reintentos que utils/api_games.py: el bot ya
llama a estas funciones desde manejadores async vía asyncio.to_thread (o
directamente, igual que hacía con gspread), así que no hace falta aiohttp acá.

Las rutas GET del Worker son públicas; las POST requieren el Bearer token.
"""

import time

import requests

from utils.secretos import d1_worker_url, d1_worker_token
from utils.logger import logger

_TIMEOUT = 10
_REINTENTOS = 3
_DELAY = 2


def _get(path: str, params: dict | None = None) -> dict | list:
    url = f"{d1_worker_url}{path}"
    ultimo_error = None
    for intento in range(1, _REINTENTOS + 1):
        try:
            resp = requests.get(url, params=params, timeout=_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            ultimo_error = e
            logger.warning(f"d1_client GET {path} - intento {intento}/{_REINTENTOS} falló: {e}")
            if intento < _REINTENTOS:
                time.sleep(_DELAY)
    logger.error(f"d1_client GET {path} - se agotaron los reintentos: {ultimo_error}")
    raise ultimo_error


def _post(path: str, payload: dict) -> dict:
    url = f"{d1_worker_url}{path}"
    headers = {"Authorization": f"Bearer {d1_worker_token}"}
    ultimo_error = None
    for intento in range(1, _REINTENTOS + 1):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            ultimo_error = e
            logger.warning(f"d1_client POST {path} - intento {intento}/{_REINTENTOS} falló: {e}")
            if intento < _REINTENTOS:
                time.sleep(_DELAY)
    logger.error(f"d1_client POST {path} - se agotaron los reintentos: {ultimo_error}")
    raise ultimo_error


def get_puntitos_all() -> list[dict]:
    return _get("/puntitos")


def upsert_puntitos(nombre: str, delta_puntos: int, delta_historico: int) -> dict:
    return _post("/puntitos/upsert", {
        "nombre": nombre, "delta_puntos": delta_puntos, "delta_historico": delta_historico,
    })


def reset_puntitos(nombre: str) -> None:
    _post("/puntitos/reset", {"nombre": nombre})


def get_victorias_all() -> list[dict]:
    return _get("/victorias")


def incrementar_victoria(nombre: str, campo: str, cant: int = 1) -> int:
    data = _post("/victorias/incrementar", {"nombre": nombre, "campo": campo, "cant": cant})
    return data["valor"]


def registrar_record_escupitajo_remoto(nombre: str, distancia: int) -> tuple[bool, int]:
    data = _post("/victorias/record_escupitajo", {"nombre": nombre, "distancia": distancia})
    return data["nuevoRecord"], data["record"]


def get_programacion() -> list[str]:
    return _get("/programacion")


def get_restricciones_escupir() -> list[dict]:
    return _get("/restricciones_escupir")


def get_daddy_points() -> int:
    data = _get("/daddy_points")
    return data["votos"]


def incrementar_daddy_points() -> int:
    data = _post("/daddy_points/incrementar", {})
    return data["votos"]


def get_claude_memoria(usuario: str) -> str:
    data = _get(f"/claude_memoria/{usuario}")
    return data["resumen"]


def set_claude_memoria(usuario: str, resumen: str) -> None:
    _post("/claude_memoria", {"usuario": usuario, "resumen": resumen})
