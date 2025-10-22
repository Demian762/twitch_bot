import os
import sys
import requests
import zipfile
from pathlib import Path

class FFmpegManager:
    def __init__(self, base_dir=None):
        self.base_dir = base_dir or os.getcwd()
        self.ffmpeg_dir = os.path.join(self.base_dir, "ffmpeg")
        self.ffmpeg_exe = os.path.join(self.ffmpeg_dir, "ffmpeg.exe")
    
    def _get_base_path(self):
        """Determina la ruta base dependiendo de si es ejecutable o script"""
        if getattr(sys, 'frozen', False):
            # Ejecutándose como .exe (PyInstaller)
            # FFmpeg debe estar en ../ffmpeg/ relativo al ejecutable
            return Path(sys.executable).parent
        else:
            # Ejecutándose como script
            # FFmpeg está en ../ffmpeg/ relativo a la carpeta bot/
            return Path(__file__).parent.parent.parent
    
    def get_ffmpeg_path(self):
        """
        Obtiene la ruta de FFmpeg con búsqueda en múltiples ubicaciones:
        1. ../ffmpeg/bin/ffmpeg.exe (para distribución)
        2. ./ffmpeg/ffmpeg.exe (actual)
        3. Descarga automática si no se encuentra
        """
        base_path = self._get_base_path()
        
        # Opción 1: FFmpeg en carpeta de distribución (../ffmpeg/bin/)
        ffmpeg_dist = base_path / 'ffmpeg' / 'bin' / 'ffmpeg.exe'
        if ffmpeg_dist.exists():
            return str(ffmpeg_dist)
        
        # Opción 2: FFmpeg en carpeta local (para desarrollo)
        if os.path.exists(self.ffmpeg_exe):
            return self.ffmpeg_exe
        
        # Opción 3: Buscar FFmpeg incluido con PyInstaller (legacy)
        if getattr(sys, 'frozen', False):
            base_pyinstaller = sys._MEIPASS
            ffmpeg_exe = os.path.join(base_pyinstaller, "ffmpeg", "ffmpeg.exe")
            if os.path.exists(ffmpeg_exe):
                return ffmpeg_exe
        
        # Opción 4: Descargar automáticamente
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
