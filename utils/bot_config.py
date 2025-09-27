from datetime import datetime

# Imports locales
from utils.api_games import rawg, steam_api
from utils.api_youtube import (
    build_yt_client,
    get_videos_list,
    get_latest_podcast,
    get_latest_video,
    get_video_details
)
from utils.utiles_general import timer_iniciar, resource_path, precio_dolar
from utils.puntitos_manager import get_programacion
from utils.logger import logger
from utils.configuracion import configuracion_basica, rutina_lista

class BotConfig:
    def __init__(self):
        try:
            self.basic = configuracion_basica
            self.dia_semana = datetime.now().strftime('%A')
            self.lista_programacion = get_programacion()
            self.rutina_lista = rutina_lista
        except Exception as e:
            logger.error(f"Error en BotConfig: {e}")
            raise

class APIManager:
    def __init__(self, rawg_url, rawg_key):
        try:
            self.rawg = rawg(rawg_url, rawg_key)
            self.steam = steam_api()
            self.yt_client = build_yt_client()
            self.dolar = precio_dolar()
            self._init_youtube_data()
        except Exception as e:
            logger.error(f"Error en APIManager: {e}")
            raise

    def _init_youtube_data(self):
        try:
            self.videos = get_videos_list(self.yt_client)
            podcast_id = get_latest_podcast(self.yt_client)
            video_id = get_latest_video(self.yt_client)
            
            nombre, link = get_video_details(podcast_id, self.yt_client)
            self.ultimo_podcast = f"{nombre} {link}"
            
            nombre, link = get_video_details(video_id, self.yt_client)
            self.ultimo_video = f"{nombre} {link}"
        except Exception as e:
            logger.error(f"Error al inicializar datos de YouTube: {e}")
            self.videos = []
            self.ultimo_podcast = "No disponible"
            self.ultimo_video = "No disponible"

class BotState:
    def __init__(self):
        self.grog_count = 0
        self.escupitajos = {}
        self.ganador = None
        self.puntitos_dados = []
        self.trivia_actual = None
        self.tiempo_iniciar = timer_iniciar()
        self.rutinas_counter = {"actual":0, "total":0}
