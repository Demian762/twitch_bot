"""
Secretos y credenciales del BotDelEstadio - TEMPLATE

IMPORTANTE: Este es un archivo TEMPLATE
- NO edites este archivo directamente
- Copia este archivo como 'secretos.py' en la misma carpeta
- Edita 'secretos.py' con tus credenciales reales

El sistema carga la configuración desde config/config.ini
Este archivo solo define la estructura y valores por defecto.

Author: Demian762
Updated: 2025-10-22
"""

from utils.config_loader import config_loader

# Configuración de Twitch
bot_channel_name = config_loader.get('TWITCH', 'bot_channel_name', 'TuBotAqui')
channel_name = config_loader.get('TWITCH', 'channel_name', 'tu_canal_aqui')
HOST = config_loader.get('TWITCH', 'host', 'irc.twitch.tv')
PORT = config_loader.get_int('TWITCH', 'port', 6667)

access_token = config_loader.get('TWITCH', 'access_token', 'tu_token_aqui')
client_id = config_loader.get('TWITCH', 'client_id', 'tu_client_id_aqui')
bot_id = config_loader.get('TWITCH', 'bot_id', 'tu_bot_id_aqui')

twitch_app_id = config_loader.get('TWITCH', 'twitch_app_id', 'tu_app_id_aqui')
twitch_app_secret = config_loader.get('TWITCH', 'twitch_app_secret', 'tu_app_secret_aqui')

# Telegram
telegram_bot_token = config_loader.get('TELEGRAM', 'telegram_bot_token', 'tu_telegram_token_aqui')

# YouTube
youtube_api_key = config_loader.get('YOUTUBE', 'youtube_api_key', 'tu_youtube_key_aqui')
hdp_channel_id = config_loader.get('YOUTUBE', 'hdp_channel_id', 'tu_channel_id_aqui')

# APIs de juegos
rawg_url = config_loader.get('GAMES', 'rawg_url', 'https://api.rawg.io/api/')
rawg_key_value = config_loader.get('GAMES', 'rawg_key', 'tu_rawg_key_aqui')
rawg_key = {'key': rawg_key_value}

steam_api_key = config_loader.get('GAMES', 'steam_api_key', 'tu_steam_key_aqui')

# ChatGPT
chat_gpt_api_key = config_loader.get('CHATGPT', 'chat_gpt_api_key', 'tu_chatgpt_key_aqui')

# Google Sheets
file_puntitos_url = config_loader.get('GOOGLE_SHEETS', 'file_puntitos_url', 'https://docs.google.com/spreadsheets/d/TU_SPREADSHEET_ID_AQUI')

# Credenciales de Google Sheets (cargadas desde config.ini)
_gspread_from_config = config_loader.get_gspread_credentials()

if _gspread_from_config:
    credenciales_gspread = _gspread_from_config
else:
    # Template básico - DEBE ser configurado en config.ini
    credenciales_gspread = {
        "type": "service_account",
        "project_id": "tu-project-id",
        "private_key_id": "tu-private-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nTU_PRIVATE_KEY_AQUI\n-----END PRIVATE KEY-----\n",
        "client_email": "tu-service-account@tu-project.iam.gserviceaccount.com",
        "client_id": "tu-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/tu-service-account%40tu-project.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }
