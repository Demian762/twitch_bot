import requests
import os
import sys


def precio_dolar():
    response = requests.get("https://dolarapi.com/v1/dolares/tarjeta")
    if response:
        print("Dólar tarjeta a: " + str(response.json()['venta']))
        return response.json()['venta']
    else:
        print("No se obtuvo el precio del dólar.")
        return 0

def get_args(args):
    respuesta = ""
    for i in args:
        respuesta = respuesta + " " + i
    respuesta = respuesta.strip().lower()
    return respuesta

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)