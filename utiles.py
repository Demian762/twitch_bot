import requests
from secretos import steam_api_key
from googleapiclient.discovery import build
from secretos import youtube_api_key, hdp_channel_id
from steam import Steam

grog_list = [
    "Una pinta de grog para el Bot!",
    "¡¡¡Otra pinta de grog para el Bot!!!",
    "Un brindis por las aventuras gráficas!!",
    "oootrhra pintita pal boott...",
    "otra maz??, bueno a ver dale....",
    "oi no manejoo.... vine en auto???",
    "pará pará ke tngo ke..... WAAAAA ..... a veh, dame dale....",
]

insultos_dict = {
    1:"¿Has dejado ya de usar pañales?",
    2:"¡No hay palabras para describir lo asqueroso que eres!",
    3:"¡He hablado con simios más educados que tu!",
    4:"¡Llevarás mi espada como si fueras un pincho moruno!",
    5:"¡Luchas como un ganadero!",
    6:"¡No pienso aguantar tu insolencia aquí sentado!",
    7:"¡Mi pañuelo limpiará tu sangre!",
    8:"¡Ha llegado tu HORA, palurdo de ocho patas!",
    9:"¡Una vez tuve un perro más listo que tu!",
    10:"¡Nadie me ha sacado sangre jamás, y nadie lo hará!",
    11:"¡Me das ganas de vomitar!",
    12:"¡Tienes los modales de un mendigo!",
    13:"¡He oído que eres un soplón despreciable!",
    14:"¡La gente cae a mis pies al verme llegar!",
    15:"¡Demasiado bobo para mi nivel de inteligencia!",
    16:"¡Obtuve esta cicatriz en una batalla a muerte!",
}

respuestas_dict = {
    1:"¿Por qué? ¿Acaso querías pedir uno prestado?",
    2:"Sí que las hay, sólo que nunca las has aprendido.",
    3:"Me alegra que asistieras a tu reunión familiar diaria.",
    4:"Primero deberías dejar de usarla como un plumero.",
    5:"Qué apropiado, tú peleas como una vaca.",
    6:"Ya te están fastidiando otra vez las almorranas, ¿Eh?",
    7:"Ah, ¿Ya has obtenido ese trabajo de barrendero?",
    8:"Y yo tengo un SALUDO para ti, ¿Te enteras?",
    9:"Te habrá enseñado todo lo que sabes.",
    10:"¿TAN rápido corres?",
    11:"Me haces pensar que alguien ya lo ha hecho.",
    12:"Quería asegurarme de que estuvieras a gusto conmigo.",
    13:"Qué pena me da que nadie haya oído hablar de ti",
    14:"¿Incluso antes de que huelan tu aliento?",
    15:"Estaría acabado si la usases alguna vez.",
    16:"Espero que ya hayas aprendido a no tocarte la nariz.",
}

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
    print(f"Obtenida la lista con " + str(len(videos)) + " videos.")
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
        playlistId = "PL14j4uHK-mdSIxw-rA9MHHHiODkdOnk72",
        maxResults=50,
    )
    response = request.execute()
    video_id = response['items'][-1]['snippet']['resourceId']['videoId']
    return video_id

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

def precio_dolar():
    response = requests.get("https://dolarapi.com/v1/dolares/tarjeta")
    if response:
        print("Dólar tarjeta a: " + str(response.json()['venta']))
        return response.json()['venta']
    else:
        print("No se obtuvo el precio del dólar.")
        return 0
