from googleapiclient.discovery import build
from utils.secretos import youtube_api_key, hdp_channel_id
from utils.logger import logger


def build_yt_client():
    yt_client = build('youtube', 'v3', developerKey=youtube_api_key)
    return yt_client

def get_videos_list(yt_client):
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

def get_latest_video(yt_client):
    request = yt_client.search().list(
        part="id",
        channelId=hdp_channel_id,
        maxResults=1,
        order="date",
        type = "video"
    )
    response = request.execute()
    video = response['items'][0]['id']['videoId']
    return video

def get_latest_podcast(yt_client):
    request = yt_client.playlistItems().list(
        part="snippet",
        playlistId = "PL14j4uHK-mdTO04RCRiFHg1NKPDv3b-sT",
        maxResults=50,
    )
    response = request.execute()
    video_id = response['items'][0]['snippet']['resourceId']['videoId']
    return video_id

def get_video_details(video_id, yt_client):
    request = yt_client.videos().list(part='snippet,statistics', id=video_id)
    response = request.execute()
    nombre_video = response['items'][0]['snippet']['title']
    nombre_video = nombre_video.split('#')[0].strip()
    link_video = "https://www.youtube.com/watch?v="+video_id
    return nombre_video, link_video
