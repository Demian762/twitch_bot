import os
import sys
import requests
import time


def precio_dolar():
    response = requests.get("https://dolarapi.com/v1/dolares/oficial")
    if response:
        print("Dólar oficial a: " + str(response.json()['venta']))
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

# funciones del timer

def timer_iniciar():
    return time.monotonic()

def timer_consulta(tiempo_iniciar):
    tiempo_actual = time.monotonic()
    diferencia = tiempo_actual - tiempo_iniciar
    horas, resto = divmod(diferencia, 3600)
    minutos, segundos = divmod(resto, 60)
    miliseg = (segundos - int(segundos)) * 1000
    return int(horas), int(minutos), int(segundos), int(miliseg)

def format_time(tiempos):
    unidades = ["horas", "minutos", "segundos", "milisegundos"]
    resultado = [
        f"{valor} {unidad[:-1] if valor == 1 else unidad}"
        for valor, unidad in zip(tiempos, unidades) if valor != 0
    ]
    return resultado