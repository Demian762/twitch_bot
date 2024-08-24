import requests
import pandas as pd
from configuracion import puntitos_file_path


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