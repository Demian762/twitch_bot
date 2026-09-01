"""
Bootstrap de secretos remotos. Se corre ANTES que cualquier otro import de
utils/ que dependa de utils/secretos.py (ver el arranque de bot_del_estadio.py).

Lee la clave remota desde .remote_key (gitignored, en la raíz del repo),
pide los secretos al worker de Cloudflare dedicado a esto (cloudflare/secrets-worker/)
y con la respuesta genera utils/secretos.py (también gitignored) para que el
resto del código lo importe exactamente igual que antes — no cambia ningún
otro call site de `from utils.secretos import ...`.

Sin conexión o con la clave inválida, el bot no arranca (a propósito: no hay
fallback con una copia vieja en disco).
"""

import os
import time

import requests

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_KEY_PATH = os.path.join(_ROOT, ".remote_key")
_SECRETOS_PATH = os.path.join(_ROOT, "utils", "secretos.py")

# No es sensible (sin la clave no sirve para nada); se puede overridear para
# apuntar a un worker local de prueba (`wrangler dev`) con la env var.
WORKER_URL = os.environ.get(
    "SECRETS_WORKER_URL", "https://botdelestadio-secrets.hdp-web.workers.dev"
)

_TIMEOUT = 10
_REINTENTOS = 3
_DELAY = 2


def _leer_clave() -> str:
    if not os.path.exists(_KEY_PATH):
        raise SystemExit(
            f"No se encontró {_KEY_PATH}. Pegá ahí la clave remota "
            "(la misma que usa el instalador) antes de arrancar el bot."
        )
    clave = open(_KEY_PATH, "r", encoding="utf-8").read().strip()
    if not clave:
        raise SystemExit(f"{_KEY_PATH} está vacío.")
    return clave


def _fetch_secrets(clave: str) -> dict[str, str]:
    url = f"{WORKER_URL}/secrets"
    headers = {"Authorization": f"Bearer {clave}"}
    ultimo_error = None
    for intento in range(1, _REINTENTOS + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=_TIMEOUT)
            if resp.status_code == 401:
                raise SystemExit("Clave remota rechazada por el worker de secretos (401).")
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            ultimo_error = e
            if intento < _REINTENTOS:
                time.sleep(_DELAY)
    raise SystemExit(
        f"No se pudo obtener los secretos remotos desde {url}: {ultimo_error}"
    )


def _escribir_secretos(valores: dict[str, str]) -> None:
    lineas = [
        "# Generado por utils/secrets_bootstrap.py en cada arranque — no editar a mano.",
        "# (gitignored; la fuente de verdad vive en el worker de secretos)",
        "",
    ]
    for nombre in sorted(valores):
        lineas.append(f"{nombre} = {valores[nombre]}")
    with open(_SECRETOS_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")


def ensure_secretos() -> None:
    clave = _leer_clave()
    valores = _fetch_secrets(clave)
    if not valores:
        raise SystemExit("El worker de secretos devolvió una lista vacía.")
    _escribir_secretos(valores)
