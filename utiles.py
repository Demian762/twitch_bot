import Levenshtein
import requests
from secretos import steam_api_key
from googleapiclient.discovery import build
from secretos import youtube_api_key, hdp_channel_id
from steam import Steam

def build_yt_client():
    yt_client = build('youtube', 'v3', developerKey=youtube_api_key)
    return yt_client

def get_videos_list(yt_client):
    request = yt_client.search().list(
        part="id",
        channelId=hdp_channel_id,
        maxResults=50,
        order="rating"
    )
    response = request.execute()
    videos = []
    for i in response['items']:
        video = i['id']['videoId']
        videos.append(video)
    print(f"Obtenida la lista con " + str(len(videos)) + " videos.")
    return videos

def get_video_details(video_id, yt_client):
    request = yt_client.videos().list(part='snippet,statistics', id=video_id)
    response = request.execute()
    nombre_video = response['items'][0]['snippet']['title']
    link_video = "https://www.youtube.com/watch?v="+video_id
    return nombre_video, link_video

def steam_api():
    try:
        steam = Steam(steam_api_key)
        print("conexión exitosa con Steam.")
        return steam
    except:
        raise "No se pudo conectar a Steam."
    
def steam_price(nombre, steam, dolar):
    try:
        steam_data = steam.apps.search_games(nombre, "AR")['apps'][0]
        precio = float(steam_data['price'].lstrip("$").rstrip(" USD"))
        precio = str(round(precio * dolar, 2))
        nombre_steam = steam_data['name']
        return nombre_steam, precio
    except:
        return False, False

def imprimir_md(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        print("El archivo no se encuentra.")

def parecidos(string_dado, lista_strings):
    mejor_coincidencia = None
    menor_distancia = float('inf')

    for string in lista_strings:
        distancia = Levenshtein.distance(string_dado, string)
        if distancia < menor_distancia:
            menor_distancia = distancia
            mejor_coincidencia = string

    return mejor_coincidencia

def precio_dolar():
    response = requests.get("https://dolarapi.com/v1/dolares/tarjeta")
    if response:
        print("Dólar tarjeta a: " + str(response.json()['venta']))
        return response.json()['venta']
    else:
        print("No se obtuvo el precio del dólar.")
        return 0