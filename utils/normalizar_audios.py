"""Nivela el loudness de los WAV del bot para que todos suenen al mismo volumen.

Uso:
    python utils/normalizar_audios.py              # todos los de storage/audios
    python utils/normalizar_audios.py a.wav b.wav  # solo esos

Mide cada archivo con el filtro ebur128 de ffmpeg (loudness integrado + true
peak), le aplica la ganancia que le falta para llegar a LOUDNESS_OBJETIVO y,
si eso hiciera pasar el pico de -1 dB, un limitador. Reescribe el archivo como
WAV 16 bits / 48 kHz. Los que ya están nivelados se dejan como están, así que
se puede correr cada vez que se agrega un audio nuevo.
"""
import glob
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOUDNESS_OBJETIVO = -18.0  # mismo valor que utils/utiles_general.py
PICO_MAX_DB = -1.0
TOLERANCIA_LU = 0.5


def _ffmpeg() -> str:
    local = os.path.join(ROOT, "ffmpeg", "ffmpeg.exe")
    if os.path.exists(local):
        return local
    encontrado = shutil.which("ffmpeg")
    if not encontrado:
        sys.exit("No se encontró ffmpeg (ni en ffmpeg/ffmpeg.exe ni en el PATH).")
    return encontrado


def medir(ffmpeg: str, path: str) -> tuple[float, float, str]:
    """Devuelve (loudness LUFS, true peak dBTP, descripción del stream de audio)."""
    out = subprocess.run(
        [ffmpeg, "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True, errors="replace",
    ).stderr
    loudness = re.findall(r"I:\s+(-?[\d.]+) LUFS", out)
    pico = re.findall(r"Peak:\s+(-?[\d.]+|-inf) dBFS", out)
    stream = re.search(r"Audio: ([^\r\n]+)", out)
    if not loudness or not pico:
        raise RuntimeError(out.strip()[-300:])
    return float(loudness[-1]), float(pico[-1]), stream.group(1) if stream else ""


def normalizar(ffmpeg: str, path: str) -> str:
    loudness, pico, stream = medir(ffmpeg, path)
    ganancia = LOUDNESS_OBJETIVO - loudness
    formato_ok = stream.startswith("pcm_s16le") and "48000 Hz" in stream
    if abs(ganancia) < TOLERANCIA_LU and pico <= PICO_MAX_DB and formato_ok:
        return f"{loudness:6.1f} LUFS  pico {pico:5.1f}  -> ya nivelado"

    filtros = f"volume={ganancia:.2f}dB"
    limitado = pico + ganancia > PICO_MAX_DB
    if limitado:
        filtros += f",alimiter=limit={10 ** (PICO_MAX_DB / 20):.3f}:level=false"

    tmp = path[:-4] + ".tmp.wav"
    result = subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", path, "-af", filtros,
         "-ar", "48000", "-c:a", "pcm_s16le", tmp],
        capture_output=True, text=True, errors="replace",
    )
    if result.returncode != 0:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise RuntimeError(result.stderr.strip()[-300:])
    os.replace(tmp, path)

    nuevo, nuevo_pico, _ = medir(ffmpeg, path)
    return (f"{loudness:6.1f} LUFS  pico {pico:5.1f}  -> {nuevo:6.1f} LUFS  pico {nuevo_pico:5.1f}"
            f"  ({ganancia:+.1f} dB{', limitado' if limitado else ''})")


def main():
    ffmpeg = _ffmpeg()
    paths = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, "storage", "audios", "*.wav")))
    errores = 0
    for path in paths:
        nombre = os.path.basename(path)
        try:
            print(f"{nombre:<22} {normalizar(ffmpeg, path)}")
        except Exception as e:
            errores += 1
            print(f"{nombre:<22} ERROR: {e}")
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
