import aiohttp
from utils.logger import logger
from utils.configuracion import discord_titulo_template


def _build_titulo_msg(titulo: str) -> str:
    return discord_titulo_template.format(titulo=titulo)


async def send_discord_message(webhook_url: str, content: str) -> bool:
    if not webhook_url:
        logger.warning("Discord webhook URL no configurada")
        return False
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json={"content": content}) as resp:
                ok = resp.status in (200, 204)
                if not ok:
                    logger.error(f"Discord webhook respondió {resp.status}")
                return ok
    except Exception as e:
        logger.error(f"Error enviando mensaje a Discord: {e}")
        return False

# Hola TheRedFallen, que haces por acá?? si descubrís este comentario y lo compartís en discord te doy 10 puntitos xD

async def notificar_titulo(webhook_url: str, titulo: str) -> bool:
    return await send_discord_message(webhook_url, _build_titulo_msg(titulo))
