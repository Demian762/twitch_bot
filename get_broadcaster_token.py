"""
Obtiene access_token + refresh_token para la cuenta del BROADCASTER (hablemosdepavadaspod).
Scope requerido: channel:bot

Uso:
    python get_broadcaster_token.py

Al finalizar, copia los tokens en utils/secretos.py bajo:
    broadcaster_access_token = '...'
    broadcaster_refresh_token = '...'
"""

import urllib.parse
import urllib.request
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from utils.secretos import twitch_app_id, twitch_app_secret

REDIRECT_URI = "http://localhost:3000"
SCOPE = "channel:bot"

captured_code = None


class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global captured_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            captured_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h2>Autorizado. Podes cerrar esta ventana.</h2>")
        else:
            error = params.get("error", ["desconocido"])[0]
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"<h2>Error: {error}</h2>".encode())

    def log_message(self, format, *args):
        pass  # silenciar logs del servidor


def get_auth_url():
    params = urllib.parse.urlencode({
        "client_id": twitch_app_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
    })
    return f"https://id.twitch.tv/oauth2/authorize?{params}"


def exchange_code(code):
    data = urllib.parse.urlencode({
        "client_id": twitch_app_id,
        "client_secret": twitch_app_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }).encode()

    req = urllib.request.Request(
        "https://id.twitch.tv/oauth2/token",
        data=data,
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main():
    auth_url = get_auth_url()
    print("Abriendo navegador para autorizar con la cuenta del BROADCASTER (hablemosdepavadaspod)...")
    print(f"\nURL: {auth_url}\n")
    webbrowser.open(auth_url)

    print("Esperando redirect en http://localhost:3000 ...")
    server = HTTPServer(("localhost", 3000), OAuthHandler)
    server.handle_request()

    if not captured_code:
        print("No se recibio el codigo de autorizacion.")
        return

    print("Codigo recibido. Obteniendo tokens...")
    tokens = exchange_code(captured_code)

    access_token = tokens.get("access_token", "")
    refresh_token = tokens.get("refresh_token", "")

    print("\n" + "=" * 60)
    print("Copia estos valores en utils/secretos.py:")
    print("=" * 60)
    print(f"broadcaster_access_token = '{access_token}'")
    print(f"broadcaster_refresh_token = '{refresh_token}'")
    print("=" * 60)


if __name__ == "__main__":
    main()
