from .telegram_voice_bot import FFmpegManager, AudioConverter

def __init__(self, token, target_chat_id=None):
    self.token = token
    self.target_chat_id = target_chat_id
    self.app = None  # No crear aquí
    self.ffmpeg_manager = FFmpegManager()
    self.converter = AudioConverter(self.ffmpeg_manager.get_ffmpeg_path())
    self.temp_files = []