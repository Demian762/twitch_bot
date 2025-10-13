from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils.secretos import youtube_api_key, hdp_channel_id
from utils.logger import logger


def build_yt_client():
    """
    Construye y retorna un cliente de la API de YouTube
    
    Returns:
        googleapiclient.discovery.Resource: Cliente de YouTube API v3
        
    Raises:
        Exception: Si falla la construcción del cliente
    """
    try:
        yt_client = build('youtube', 'v3', developerKey=youtube_api_key)
        return yt_client
    except Exception as e:
        logger.error(f"Error al construir cliente de YouTube: {e}")
        raise

def get_videos_list(yt_client):
    """
    Obtiene una lista de videos del canal ordenados por rating
    
    Args:
        yt_client: Cliente de la API de YouTube
        
    Returns:
        list: Lista de IDs de videos
        
    Raises:
        Exception: Si falla la consulta a la API
    """
    try:
        request = yt_client.search().list(
            part="id",
            channelId=hdp_channel_id,
            maxResults=50,
            order="rating",
            type = "video"
        )
        response = request.execute()
        videos = []
        for i in response['items']:
            video = i['id']['videoId']
            videos.append(video)
        logger.info(f"Obtenida la lista con " + str(len(videos)) + " videos.")
        return videos
    except HttpError as e:
        logger.error(f"Error HTTP en get_videos_list: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado en get_videos_list: {e}")
        raise

def get_latest_video(yt_client):
    """
    Obtiene el video más reciente del canal
    
    Args:
        yt_client: Cliente de la API de YouTube
        
    Returns:
        str: ID del video más reciente
        
    Raises:
        Exception: Si falla la consulta a la API o no hay videos
    """
    try:
        request = yt_client.search().list(
            part="id",
            channelId=hdp_channel_id,
            maxResults=1,
            order="date",
            type = "video"
        )
        response = request.execute()
        if not response['items']:
            raise Exception("No se encontraron videos en el canal")
        video = response['items'][0]['id']['videoId']
        return video
    except HttpError as e:
        logger.error(f"Error HTTP en get_latest_video: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado en get_latest_video: {e}")
        raise

def get_latest_podcast(yt_client):
    """
    Obtiene el podcast más reciente de la playlist de podcasts
    
    Args:
        yt_client: Cliente de la API de YouTube
        
    Returns:
        str: ID del video del podcast más reciente
        
    Raises:
        Exception: Si falla la consulta a la API o no hay podcasts
    """
    try:
        request = yt_client.playlistItems().list(
            part="snippet",
            playlistId = "PL14j4uHK-mdTO04RCRiFHg1NKPDv3b-sT",
            maxResults=50,
        )
        response = request.execute()
        if not response['items']:
            raise Exception("No se encontraron podcasts en la playlist")
        video_id = response['items'][0]['snippet']['resourceId']['videoId']
        return video_id
    except HttpError as e:
        logger.error(f"Error HTTP en get_latest_podcast: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado en get_latest_podcast: {e}")
        raise

def get_video_details(video_id, yt_client):
    """
    Obtiene los detalles de un video específico
    
    Args:
        video_id (str): ID del video
        yt_client: Cliente de la API de YouTube
        
    Returns:
        tuple: (nombre_video, link_video)
        
    Raises:
        Exception: Si falla la consulta a la API o no se encuentra el video
    """
    try:
        request = yt_client.videos().list(part='snippet,statistics', id=video_id)
        response = request.execute()
        if not response['items']:
            raise Exception(f"No se encontró el video con ID: {video_id}")
        nombre_video = response['items'][0]['snippet']['title']
        nombre_video = nombre_video.split('#')[0].strip()
        link_video = "https://www.youtube.com/watch?v="+video_id
        return nombre_video, link_video
    except HttpError as e:
        logger.error(f"Error HTTP en get_video_details: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado en get_video_details: {e}")
        raise
