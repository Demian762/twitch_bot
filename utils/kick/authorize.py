"""
Script de autorización de Kick — correr UNA SOLA VEZ (o de nuevo si se pierde
el archivo .kick.tokens.json o se quieren cambiar los scopes autorizados):

    bot-env\\Scripts\\python.exe -m utils.kick.authorize

Abre el navegador para loguear y autorizar la app de Kick, y guarda los
tokens en .kick.tokens.json junto al script/exe.
"""

from utils.secrets_bootstrap import ensure_secretos
ensure_secretos()

from utils.kick.auth import run_authorization_flow

if __name__ == "__main__":
    run_authorization_flow()
