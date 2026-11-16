import io
import os
import sys
import wave
import ctypes
import asyncio
import functools
import subprocess
import tempfile
import threading
import winsound
import requests
import time
from utils.logger import logger

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_AUDIOS_DIR = os.path.join(_ROOT, 'storage')
_AUDIO_MUTED_FLAG  = os.path.join(_ROOT, '.audio_muted')
_AUDIO_VOLUME_FILE = os.path.join(_ROOT, '.audio_volume')
_TTS_MUTED_FLAG    = os.path.join(_ROOT, '.tts_muted')
_TTS_VOICE  = "es-AR-TomasNeural"
_TTS_RATE   = "+15%"
_TTS_PITCH  = "-20Hz"

# Volumen elegido en el launcher (bot_launcher.pyw escribe .audio_volume):
# 10 niveles, el 6 reproduce el audio tal cual y cada nivel suma/resta 3 dB.
VOLUMEN_NIVELES = 10
VOLUMEN_DEFAULT = 6
_DB_POR_NIVEL = 3.0
# Loudness al que están nivelados los WAV de storage/audios (utils/normalizar_audios.py);
# la voz TTS y los audios de Telegram se llevan a este mismo nivel al reproducirse.
LOUDNESS_OBJETIVO = -18.0
_LIMITE_PICO = 0.89  # ~ -1 dBFS, para que subir el volumen no recorte

_audio_lock = threading.Lock()

def tts_habilitado() -> bool:
    return not os.path.exists(_TTS_MUTED_FLAG)

def nivel_volumen() -> int:
    try:
        with open(_AUDIO_VOLUME_FILE) as f:
            return min(max(int(f.read().strip()), 1), VOLUMEN_NIVELES)
    except (OSError, ValueError):
        return VOLUMEN_DEFAULT

def _ganancia_db() -> float:
    return (nivel_volumen() - VOLUMEN_DEFAULT) * _DB_POR_NIVEL

def _filtro_volumen(ganancia_db: float) -> str:
    filtro = f"volume={ganancia_db:.1f}dB"
    if ganancia_db > 0:
        filtro += f",alimiter=limit={_LIMITE_PICO}:level=false"
    return filtro

@functools.cache
def _ffmpeg_path() -> str | None:
    try:
        from telegram_bot.ffmpeg_manager import FFmpegManager
        return FFmpegManager().get_ffmpeg_path()
    except Exception as e:
        logger.warning(f"Audio: no se encontró ffmpeg, se reproduce sin ajustar volumen ({e})")
        return None

def _render_wav(src: str, filtros: str) -> bytes | None:
    """Pasa `src` por ffmpeg con los filtros dados y devuelve un WAV
    (16 bits / 48 kHz / estéreo) en memoria, o None si falla."""
    ffmpeg = _ffmpeg_path()
    if not ffmpeg:
        return None
    try:
        result = subprocess.run(
            [ffmpeg, '-hide_banner', '-loglevel', 'error', '-i', src, '-af', filtros,
             '-ar', '48000', '-ac', '2', '-f', 's16le', '-'],
            capture_output=True, timeout=60, creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        logger.warning(f"Audio: ffmpeg falló con {os.path.basename(src)}: {e}")
        return None
    if result.returncode != 0 or not result.stdout:
        logger.warning(f"Audio: ffmpeg falló con {os.path.basename(src)}: "
                       f"{result.stderr.decode(errors='replace').strip()[-200:]}")
        return None
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(48000)
        w.writeframes(result.stdout)
    return buf.getvalue()

@functools.lru_cache(maxsize=32)
def _render_wav_cacheado(path: str, _mtime: float, ganancia_db: float) -> bytes | None:
    return _render_wav(path, _filtro_volumen(ganancia_db))

def _con_volumen(path: str, flags: int = winsound.SND_FILENAME) -> tuple[str | bytes, int]:
    """Devuelve (sonido, flags) para PlaySound con el volumen del launcher
    aplicado. En el nivel por defecto, o si algo falla, el archivo tal cual."""
    ganancia = _ganancia_db()
    # SND_MEMORY no admite SND_ASYNC
    if ganancia == 0 or flags & winsound.SND_ASYNC or not flags & winsound.SND_FILENAME:
        return path, flags
    try:
        if os.path.normcase(os.path.abspath(path)).startswith(os.path.normcase(_AUDIOS_DIR)):
            # Los audios fijos del bot se cachean; los temporales (Telegram) no.
            data = _render_wav_cacheado(path, os.path.getmtime(path), ganancia)
        else:
            data = _render_wav(path, _filtro_volumen(ganancia))
    except OSError:
        data = None
    if data is None:
        return path, flags
    return data, (flags & ~winsound.SND_FILENAME) | winsound.SND_MEMORY

def play_sound(path: str, flags: int = winsound.SND_FILENAME, bypass_mute: bool = False) -> None:
    if bypass_mute or not os.path.exists(_AUDIO_MUTED_FLAG):
        sound, flags = _con_volumen(path, flags)
        with _audio_lock:
            winsound.PlaySound(sound, flags)

def play_sounds_sequential(*paths: str, bypass_mute: bool = False) -> None:
    """Reproduce varios sonidos en secuencia de forma bloqueante y exclusiva."""
    if bypass_mute or not os.path.exists(_AUDIO_MUTED_FLAG):
        sounds = [_con_volumen(path) for path in paths]
        with _audio_lock:
            for sound, flags in sounds:
                winsound.PlaySound(sound, flags)

def _play_mci(path: str) -> None:
    mci = ctypes.windll.winmm.mciSendStringW
    alias = f"tts_{id(path)}"
    tipo = "waveaudio" if path.lower().endswith(".wav") else "mpegvideo"
    mci(f'open "{path}" type {tipo} alias {alias}', None, 0, None)
    mci(f'play {alias} wait', None, 0, None)
    mci(f'close {alias}', None, 0, None)

async def play_tts(text: str) -> None:
    if os.path.exists(_TTS_MUTED_FLAG):
        return
    tmp = tmp_wav = None
    try:
        import edge_tts
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            tmp = f.name
        await edge_tts.Communicate(text, _TTS_VOICE, rate=_TTS_RATE, pitch=_TTS_PITCH).save(tmp)
        # Nivelar la voz al mismo loudness que los audios y aplicar el volumen
        # del launcher; si ffmpeg no está, se reproduce el mp3 tal cual.
        filtros = f"loudnorm=I={LOUDNESS_OBJETIVO}:TP=-1.5:LRA=11,{_filtro_volumen(_ganancia_db())}"
        data = await asyncio.to_thread(_render_wav, tmp, filtros)
        if data:
            tmp_wav = tmp[:-4] + '.wav'
            with open(tmp_wav, 'wb') as f:
                f.write(data)
        await asyncio.to_thread(_play_mci, tmp_wav or tmp)
    except Exception as e:
        logger.warning(f"TTS: {e}")
    finally:
        for path in (tmp, tmp_wav):
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
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
