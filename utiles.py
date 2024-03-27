import Levenshtein
import requests
from twitch_secrets import steam_api_key
from steam import Steam

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