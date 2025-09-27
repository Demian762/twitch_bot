import os
import sys
import requests
import time
from utils.logger import logger


def precio_dolar():
    response = requests.get("https://dolarapi.com/v1/dolares/oficial")
    if response:
        logger.info("Dólar oficial a: " + str(response.json()['venta']))
        return response.json()['venta']
    else:
        logger.warning("No se obtuvo el precio del dólar.")
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

def validate_dice_format(formato):
    cantidad_permitida = 20
    caras_permitidas = [4, 6, 8, 12, 20]

    if not formato:
        return None
        
    try:
        # Convertir a minúscula y separar cantidad y caras
        formato = formato.lower()
        if 'd' not in formato:
            return None
            
        cantidad, caras = formato.split('d')
        
        # Convertir a enteros
        cantidad = int(cantidad)
        caras = int(caras)
        
        # Validar límites
        if cantidad < 1 or cantidad > cantidad_permitida:
            return None
            
        if caras not in caras_permitidas:
            return None
            
        # Devolver el formato validado
        return f"{cantidad}d{caras}"
        
    except (ValueError, AttributeError):
        return None
