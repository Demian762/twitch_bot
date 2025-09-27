import os
import subprocess

class AudioConverter:
    def __init__(self, ffmpeg_path):
        self.ffmpeg_path = ffmpeg_path
    
    def convert_opus_to_wav(self, ogg_path):
        if not self.ffmpeg_path:
            return None
        
        try:
            wav_path = ogg_path.replace('.ogg', '.wav')
            cmd = [
                self.ffmpeg_path, '-i', ogg_path,
                '-ar', '44100', '-ac', '1', '-acodec', 'pcm_s16le',
                '-y', wav_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(wav_path):
                return wav_path
            return None
        except:
            return None