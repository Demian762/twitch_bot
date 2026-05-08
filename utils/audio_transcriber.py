"""
Transcripción de micrófono en tiempo real usando faster-whisper.

Captura audio del micrófono en chunks de CHUNK_SECONDS segundos y transcribe
localmente con Whisper. Llama al callback asíncrono con cada fragmento reconocido.

Deps (opcionales — el bot arranca sin ellas):
    pip install sounddevice faster-whisper
"""

import threading
import asyncio
import numpy as np

from utils.logger import logger

MODELO_DEFAULT = "small"
SAMPLE_RATE = 16000
CHUNK_SECONDS = 5
SILENCE_THRESHOLD = 0.01


class AudioTranscriber:

    def __init__(self, model_size: str = MODELO_DEFAULT):
        self._model_size = model_size
        self._model = None
        self._running = False
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._callback = None

    def _load_model(self) -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise ImportError("faster-whisper no instalado — ejecutá: pip install faster-whisper")
        logger.info(f"[mic] Cargando modelo Whisper '{self._model_size}'...")
        self._model = WhisperModel(self._model_size, device="cpu", compute_type="int8")
        logger.info("[mic] Modelo listo")

    def _transcribe(self, audio: np.ndarray) -> str:
        if np.abs(audio).max() < SILENCE_THRESHOLD:
            return ""
        segments, _ = self._model.transcribe(
            audio, language="es", vad_filter=True, beam_size=5
        )
        return " ".join(seg.text for seg in segments).strip()

    def _record_loop(self) -> None:
        try:
            import sounddevice as sd
        except ImportError:
            logger.error("[mic] sounddevice no instalado — ejecutá: pip install sounddevice")
            return
        try:
            self._load_model()
        except Exception as e:
            logger.error(f"[mic] No se pudo cargar el modelo: {e}")
            return

        chunk_frames = int(SAMPLE_RATE * CHUNK_SECONDS)
        while self._running:
            try:
                audio = sd.rec(chunk_frames, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
                sd.wait()
                if not self._running:
                    break
                text = self._transcribe(audio.flatten())
                if text and self._callback and self._loop:
                    asyncio.run_coroutine_threadsafe(self._callback(text), self._loop)
            except Exception as e:
                if self._running:
                    logger.error(f"[mic] Error en loop de grabación: {e}")

    def start(self, loop: asyncio.AbstractEventLoop, callback) -> None:
        self._loop = loop
        self._callback = callback
        self._running = True
        self._thread = threading.Thread(
            target=self._record_loop, daemon=True, name="audio-transcriber"
        )
        self._thread.start()
        logger.info("[mic] Transcriptor de micrófono iniciado")

    def stop(self) -> None:
        self._running = False
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass
        logger.info("[mic] Transcriptor de micrófono detenido")
