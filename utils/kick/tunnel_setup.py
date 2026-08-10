"""
Asegura que los archivos que cloudflared necesita para levantar el túnel
(cert.pem, <tunnel-id>.json y config.yml en ~/.cloudflared/) existan en esta
máquina, generándolos desde utils/secretos.py si faltan.

Esto evita tener que copiar la carpeta ~/.cloudflared a mano a cada PC nueva:
alcanza con pasar secretos.py, que ya es como se distribuyen las demás
credenciales de este bot (ver CLAUDE.md, sección Credenciales).
"""

import json
import os

from utils.configuracion import kick_config
from utils.logger import logger

try:
    from utils.secretos import kick_cloudflare_cert_pem, kick_cloudflare_tunnel_credentials
except ImportError:
    kick_cloudflare_cert_pem = None
    kick_cloudflare_tunnel_credentials = None


def _cloudflared_dir(base_dir: str | None = None) -> str:
    base = base_dir if base_dir is not None else os.path.expanduser("~")
    return os.path.join(base, ".cloudflared")


def ensure_tunnel_files(base_dir: str | None = None) -> str | None:
    """Crea cert.pem / <tunnel-id>.json / config.yml si no existen, usando
    los valores de secretos.py.

    Args:
        base_dir: solo para tests — reemplaza el home del usuario real.

    Returns:
        El nombre del tunnel a pasarle a `cloudflared tunnel run`, o None
        si no hay tunnel configurado en kick_config.
    """
    tunnel_name = kick_config.get("cloudflare_tunnel_name")
    if not tunnel_name:
        return None

    cf_dir = _cloudflared_dir(base_dir)
    os.makedirs(cf_dir, exist_ok=True)

    cert_path = os.path.join(cf_dir, "cert.pem")
    if not os.path.exists(cert_path):
        if not kick_cloudflare_cert_pem:
            logger.warning(
                "[kick_tunnel] Falta cert.pem y no hay kick_cloudflare_cert_pem en secretos.py"
            )
        else:
            # newline="" evita que Windows convierta los \n del string a
            # \r\n al escribir — cloudflared generó el original con LF puro.
            with open(cert_path, "w", encoding="utf-8", newline="") as f:
                f.write(kick_cloudflare_cert_pem)
            logger.info(f"[kick_tunnel] cert.pem creado en {cert_path}")

    tunnel_id = (kick_cloudflare_tunnel_credentials or {}).get("TunnelID")
    creds_path = os.path.join(cf_dir, f"{tunnel_id}.json") if tunnel_id else None

    if creds_path and not os.path.exists(creds_path):
        with open(creds_path, "w", encoding="utf-8", newline="") as f:
            json.dump(kick_cloudflare_tunnel_credentials, f, separators=(",", ":"))
        logger.info(f"[kick_tunnel] Credenciales del tunnel creadas en {creds_path}")

    config_path = os.path.join(cf_dir, "config.yml")
    if not os.path.exists(config_path) and tunnel_id and creds_path:
        hostname = kick_config.get("webhook_public_hostname", "")
        port = kick_config["webhook_port"]
        content = (
            f"tunnel: {tunnel_id}\n"
            f"credentials-file: {creds_path}\n"
            "\n"
            "ingress:\n"
            f"  - hostname: {hostname}\n"
            f"    service: http://localhost:{port}\n"
            "  - service: http_status:404\n"
        )
        with open(config_path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        logger.info(f"[kick_tunnel] config.yml creado en {config_path}")

    return tunnel_name
