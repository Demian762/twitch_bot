import Levenshtein
from twitch_secrets import steam_api_key
from steam import Steam

def steam_api():
    steam = Steam(steam_api_key)
    print("conexión exitosa con Steam.")
    return steam

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