import os
import sys
import ctypes
import asyncio
import tempfile
import threading
import winsound
import requests
import time
from utils.logger import logger

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_AUDIO_MUTED_FLAG = os.path.join(_ROOT, '.audio_muted')
_TTS_MUTED_FLAG   = os.path.join(_ROOT, '.tts_muted')
_TTS_VOICE  = "es-AR-TomasNeural"
_TTS_RATE   = "+15%"
_TTS_PITCH  = "-20Hz"

_audio_lock = threading.Lock()

def tts_habilitado() -> bool:
    return not os.path.exists(_TTS_MUTED_FLAG)

def play_sound(path: str, flags: int = winsound.SND_FILENAME, bypass_mute: bool = False) -> None:
    if bypass_mute or not os.path.exists(_AUDIO_MUTED_FLAG):
        with _audio_lock:
            winsound.PlaySound(path, flags)

def play_sounds_sequential(*paths: str, bypass_mute: bool = False) -> None:
    """Reproduce varios sonidos en secuencia de forma bloqueante y exclusiva."""
    if bypass_mute or not os.path.exists(_AUDIO_MUTED_FLAG):
        with _audio_lock:
            for path in paths:
                winsound.PlaySound(path, winsound.SND_FILENAME)

def _play_mp3(path: str) -> None:
    mci = ctypes.windll.winmm.mciSendStringW
    alias = f"tts_{id(path)}"
    mci(f'open "{path}" type mpegvideo alias {alias}', None, 0, None)
    mci(f'play {alias} wait', None, 0, None)
    mci(f'close {alias}', None, 0, None)

async def play_tts(text: str) -> None:
    if os.path.exists(_TTS_MUTED_FLAG):
        return
    tmp = None
    try:
        import edge_tts
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            tmp = f.name
        await edge_tts.Communicate(text, _TTS_VOICE, rate=_TTS_RATE, pitch=_TTS_PITCH).save(tmp)
        await asyncio.to_thread(_play_mp3, tmp)
    except Exception as e:
        logger.warning(f"TTS: {e}")
    finally:
        if tmp and os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass


def precio_dolar():
    response = requests.get("https://dolarapi.com/v1/dolares/oficial", timeout=10)
    if response.status_code == 200:
        data = response.json()
        venta = data.get('venta', 0)
        logger.info("Dólar oficial a: " + str(venta))
        return venta
    else:
        logger.warning(f"Error al obtener el precio del dólar. Status code: {response.status_code}")
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
