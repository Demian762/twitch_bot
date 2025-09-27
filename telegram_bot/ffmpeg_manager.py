import os
import sys
import requests
import zipfile

class FFmpegManager:
    def __init__(self, base_dir=None):
        self.base_dir = base_dir or os.getcwd()
        self.ffmpeg_dir = os.path.join(self.base_dir, "ffmpeg")
        self.ffmpeg_exe = os.path.join(self.ffmpeg_dir, "ffmpeg.exe")
    
    def get_ffmpeg_path(self):
        # Buscar FFmpeg incluido con PyInstaller
        if getattr(sys, 'frozen', False):
            # Ejecutándose como .exe
            base_path = sys._MEIPASS
            ffmpeg_exe = os.path.join(base_path, "ffmpeg", "ffmpeg.exe")
            if os.path.exists(ffmpeg_exe):
                return ffmpeg_exe
        
        # Fallback: método actual
        if os.path.exists(self.ffmpeg_exe):
            return self.ffmpeg_exe
        return self._download_ffmpeg()
    
    def _download_ffmpeg(self):
        try:
            url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
            response = requests.get(url, stream=True)
            zip_path = "ffmpeg.zip"
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                for file in zip_file.namelist():
                    if file.endswith('ffmpeg.exe'):
                        zip_file.extract(file)
                        os.makedirs(self.ffmpeg_dir, exist_ok=True)
                        os.rename(file, self.ffmpeg_exe)
                        break
            
            os.unlink(zip_path)
            return self.ffmpeg_exe
        except:
            return None
