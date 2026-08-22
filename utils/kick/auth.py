"""
Autenticación OAuth 2.1 + PKCE contra la API de Kick.

Flujo:
  1. run_authorization_flow() — se corre UNA VEZ de forma interactiva
     (python -m utils.kick.authorize): abre el navegador, el usuario loguea
     y autoriza la app, un servidor HTTP local efímero captura el ?code=...
     del redirect_uri, se canjea por tokens y se guardan en disco.
  2. get_access_token() — usado por el bot en cada arranque; devuelve un
     access_token válido, refrescándolo contra la API si venció.

Referencia: https://github.com/KickEngineering/KickDevDocs
"""

import asyncio
import base64
import hashlib
import http.server
import json
import os
import secrets
import sys
import time
import urllib.parse
import webbrowser

import aiohttp

from utils.configuracion import kick_config
from utils.logger import logger
from utils.secretos import kick_client_id, kick_client_secret, kick_redirect_uri

AUTHORIZE_URL = "https://id.kick.com/oauth/authorize"
TOKEN_URL = "https://id.kick.com/oauth/token"

_REFRESH_MARGIN_SECONDS = 60  # renovar un poco antes de que venza de verdad

# Cache en memoria de los tokens del proceso del bot, para no releer y
# reparsear .kick.tokens.json en cada request REST (get_access_token() se
# llama antes de cada una). Solo se actualiza al cargar por primera vez o al
# refrescar — si se re-corre `python -m utils.kick.authorize` con el bot ya
# corriendo, no lo va a notar hasta el próximo reinicio.
_cached_tokens: dict | None = None
_refresh_lock = asyncio.Lock()


def _token_file_path() -> str:
    """Ruta del archivo de tokens de Kick, junto al exe/script (igual que .tio.tokens.json).

    Este archivo vive en utils/kick/auth.py, dos niveles bajo la raíz del
    proyecto (utils/kick/), así que hacen falta 3 dirname() para llegar a la
    raíz: utils/kick -> utils -> raíz.
    """
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, ".kick.tokens.json")


def _generate_pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode("ascii")
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def _load_tokens() -> dict | None:
    path = _token_file_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"[kick_auth] No se pudo leer {path}: {e}")
        return None


def _save_tokens(data: dict) -> None:
    global _cached_tokens
    path = _token_file_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        logger.error(f"[kick_auth] No se pudo guardar {path}: {e}")
    _cached_tokens = data


def _get_cached_tokens() -> dict | None:
    global _cached_tokens
    if _cached_tokens is None:
        _cached_tokens = _load_tokens()
    return _cached_tokens


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    """Maneja el único GET del redirect_uri y guarda code/state/error en el server."""

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        self.server.auth_code = params.get("code", [None])[0]
        self.server.auth_state = params.get("state", [None])[0]
        self.server.auth_error = params.get("error", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        if self.server.auth_error:
            body = f"<h1>Error de autorización</h1><p>{self.server.auth_error}</p>"
        else:
            body = "<h1>Listo!</h1><p>Ya podés cerrar esta pestaña y volver a la terminal.</p>"
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, format, *args) -> None:
        return  # silenciar el log de acceso HTTP default en consola


def _wait_for_callback(port: int) -> tuple[str | None, str | None, str | None]:
    server = http.server.HTTPServer(("127.0.0.1", port), _CallbackHandler)
    server.auth_code = None
    server.auth_state = None
    server.auth_error = None
    try:
        server.handle_request()  # bloquea hasta recibir UNA sola request
    finally:
        server.server_close()
    return server.auth_code, server.auth_state, server.auth_error


async def _exchange_code(code: str, verifier: str) -> dict:
    data = {
        "code": code,
        "client_id": kick_client_id,
        "client_secret": kick_client_secret,
        "redirect_uri": kick_redirect_uri,
        "grant_type": "authorization_code",
        "code_verifier": verifier,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(TOKEN_URL, data=data) as resp:
            if resp.status >= 400:
                body = await resp.text()
                raise RuntimeError(f"Kick rechazó el canje del code ({resp.status}): {body}")
            return await resp.json()


async def _refresh(refresh_token: str) -> dict:
    data = {
        "refresh_token": refresh_token,
        "client_id": kick_client_id,
        "client_secret": kick_client_secret,
        "grant_type": "refresh_token",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(TOKEN_URL, data=data) as resp:
            if resp.status >= 400:
                body = await resp.text()
                raise RuntimeError(f"Kick rechazó el refresh ({resp.status}): {body}")
            return await resp.json()


def run_authorization_flow() -> None:
    """
    Flujo interactivo de autorización — correr UNA VEZ:
        bot-env\\Scripts\\python.exe -m utils.kick.authorize

    Abre el navegador para que el usuario loguee en Kick y autorice la app,
    captura el code con un servidor HTTP local efímero en kick_redirect_uri,
    lo canjea por tokens y los guarda en disco. No requiere un event loop
    corriendo de antes (lo crea internamente para el canje).
    """
    if not kick_client_id or not kick_client_secret:
        raise RuntimeError(
            "Faltan kick_client_id / kick_client_secret en utils/secretos.py. "
            "Registrá la app primero en https://kick.com/settings/developer "
            "(requiere 2FA activado en la cuenta de Kick)."
        )

    verifier, challenge = _generate_pkce_pair()
    state = secrets.token_urlsafe(16)

    params = {
        "client_id": kick_client_id,
        "response_type": "code",
        "redirect_uri": kick_redirect_uri,
        "state": state,
        "scope": kick_config["scopes"],
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    url = f"{AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"
    port = urllib.parse.urlparse(kick_redirect_uri).port or kick_config["oauth_callback_port"]

    print(f"Abriendo el navegador para autorizar la app de Kick...\n{url}")
    webbrowser.open(url)

    code, returned_state, error = _wait_for_callback(port)

    if error:
        raise RuntimeError(f"Kick rechazó la autorización: {error}")
    if not code:
        raise RuntimeError("No se recibió ningún código de autorización.")
    if returned_state != state:
        raise RuntimeError("El 'state' devuelto no coincide con el enviado — abortando por seguridad.")

    token_data = asyncio.run(_exchange_code(code, verifier))
    token_data["obtained_at"] = time.time()
    _save_tokens(token_data)
    print("Cuenta de Kick conectada y tokens guardados correctamente.")


async def get_access_token() -> str:
    """
    Devuelve un access_token válido, refrescándolo si venció.

    Raises:
        RuntimeError: si todavía no se corrió run_authorization_flow() al menos una vez.
    """
    tokens = _get_cached_tokens()
    if tokens is None:
        raise RuntimeError(
            "No hay tokens de Kick guardados. Corré primero: "
            "bot-env\\Scripts\\python.exe -m utils.kick.authorize"
        )

    expires_at = tokens.get("obtained_at", 0) + tokens.get("expires_in", 0)
    if time.time() < expires_at - _REFRESH_MARGIN_SECONDS:
        return tokens["access_token"]

    # Lock + doble chequeo: si dos requests pisan el vencimiento casi juntas,
    # solo la primera refresca de verdad; la segunda ve el token ya renovado
    # al entrar al lock y no dispara un segundo refresh con el mismo
    # refresh_token (Kick puede invalidarlo al usarlo una vez).
    async with _refresh_lock:
        tokens = _cached_tokens
        expires_at = tokens.get("obtained_at", 0) + tokens.get("expires_in", 0)
        if time.time() < expires_at - _REFRESH_MARGIN_SECONDS:
            return tokens["access_token"]

        logger.info("[kick_auth] access_token vencido, refrescando...")
        refreshed = await _refresh(tokens["refresh_token"])
        refreshed["obtained_at"] = time.time()
        # Kick puede no devolver un refresh_token nuevo en cada refresh; conservar el viejo si falta
        refreshed.setdefault("refresh_token", tokens["refresh_token"])
        _save_tokens(refreshed)
        return refreshed["access_token"]
