"""
Transcripción de micrófono en tiempo real usando faster-whisper.

Graba micro-chunks de MICRO_CHUNK_S segundos y acumula audio mientras hay voz.
Cuando detecta silencio sostenido (>= SILENCE_DURATION_S), corta y transcribe
el buffer completo como una sola oración. Esto evita partir frases en el medio.

Deps (opcionales — el bot arranca sin ellas):
    pip install sounddevice faster-whisper
"""

import threading
import asyncio
import numpy as np

from utils.logger import logger

MODELO_DEFAULT  = "small"
SAMPLE_RATE     = 16000
MICRO_CHUNK_S   = 0.3   # granularidad de detección de silencio
SILENCE_THRESHOLD  = 0.015  # amplitud máxima para considerar silencio
SILENCE_DURATION_S = 0.8    # silencio sostenido que corta una oración
MIN_UTTERANCE_S    = 0.6    # duración mínima para intentar transcribir
MAX_UTTERANCE_S    = 30.0   # corte forzado si la oración es muy larga
MIN_SPEECH_RMS     = 0.02   # energía RMS mínima del habla para no alucinaciones

# Vocabulario del canal: sesga al modelo a deletrear bien estas palabras
INITIAL_PROMPT = "Bot del Estadio, Claudio, Hablemos de Pavadas, Demian"


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
        segments, _ = self._model.transcribe(
            audio, language="es", vad_filter=True, beam_size=5,
            initial_prompt=INITIAL_PROMPT,
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

        micro_frames         = int(SAMPLE_RATE * MICRO_CHUNK_S)
        silence_needed       = int(SILENCE_DURATION_S / MICRO_CHUNK_S)  # micro-chunks consecutivos de silencio
        min_speech_frames    = int(MIN_UTTERANCE_S * SAMPLE_RATE)
        max_speech_frames    = int(MAX_UTTERANCE_S * SAMPLE_RATE)

        buffer: list[np.ndarray] = []
        silence_count = 0

        while self._running:
            try:
                chunk = sd.rec(micro_frames, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
                sd.wait()
                if not self._running:
                    break

                flat = chunk.flatten()
                is_silent = np.abs(flat).max() < SILENCE_THRESHOLD

                if is_silent:
                    if buffer:
                        # Incluir silencio al final para contexto natural de Whisper
                        buffer.append(flat)
                        silence_count += 1
                else:
                    silence_count = 0
                    buffer.append(flat)

                total_frames = sum(len(c) for c in buffer)
                should_cut = (
                    (silence_count >= silence_needed and total_frames >= min_speech_frames)
                    or total_frames >= max_speech_frames
                )

                if should_cut:
                    audio = np.concatenate(buffer)
                    buffer = []
                    silence_count = 0
                    # Verificar energía mínima antes de transcribir para evitar alucinaciones
                    speech_frames = audio[np.abs(audio) >= SILENCE_THRESHOLD]
                    if len(speech_frames) == 0 or np.sqrt(np.mean(speech_frames ** 2)) < MIN_SPEECH_RMS:
                        continue
                    text = self._transcribe(audio)
                    if text and self._callback and self._loop:
                        asyncio.run_coroutine_threadsafe(self._callback(text), self._loop)

            except Exception as e:
                if self._running:
                    logger.error(f"[mic] Error en loop: {e}")

    def start(self, loop: asyncio.AbstractEventLoop, callback) -> None:
        self._loop = loop
        self._callback = callback
        self._running = True
        self._thread = threading.Thread(
            target=self._record_loop, daemon=True, name="audio-transcriber"
        )
        self._thread.start()
        logger.info("[mic] Transcriptor de micrófono iniciado (VAD por silencio)")

    def stop(self) -> None:
        self._running = False
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass
        logger.info("[mic] Transcriptor de micrófono detenido")
