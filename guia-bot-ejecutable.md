# 🤖 Guía de Instalación y Compilación - BotDelEstadio

## 📋 Requisitos Previos
- **Python 3.11+** instalado en el sistema
- **Git** para clonado del repositorio
- **Windows** (para reproducción de audio y compilación)

---

## 🏗️ Para instalar en local desde requirements.txt:

### Opción 1: Instalación automática (recomendada)
```bash
pip install -r requirements.txt
```

### Opción 2: Instalación manual (si hay problemas)
```bash
pip install playsound
pip install python-Levenshtein
pip install -U twitchio
pip install howlongtobeatpy==1.0.18
pip install python-steam-api
pip install google-api-python-client
pip install gspread
pip install requests
pip install pandas
pip install pyinstaller
```

---

## 🚀 Para correrlo sin compilar

### En Windows PowerShell:
```powershell
cd "ruta\al\proyecto"
.\bot-env\Scripts\activate.bat
python bot_del_estadio.py
```

### En Git Bash:
```bash
cd /ruta/al/proyecto
source bot-env/Scripts/activate
python bot_del_estadio.py
```

---

## 📦 Para crear ejecutable distribuible:

### ⚠️ IMPORTANTE: Usar PyInstaller desde el entorno virtual

#### Comando actualizado (2025):
```powershell
cd "D:\02 - practicas Python\00_twitch_bot"
.\bot-env\Scripts\pyinstaller.exe --onefile --add-data "storage/*;storage" --add-data "telegram_bot;telegram_bot" --add-binary "D:\02 - practicas Python\00_twitch_bot\ffmpeg\ffmpeg.exe;ffmpeg" --add-binary "D:\02 - practicas Python\00_twitch_bot\bot-env\Lib\site-packages\fake_useragent\data\browsers.json;fake_useragent/data" bot_del_estadio.py
```

#### Parámetros explicados:
- `--onefile`: Crea un solo archivo ejecutable
- `--add-data "storage/*;storage"`: Incluye archivos de audio
- `--add-data "telegram_bot;telegram_bot"`: Incluye módulo de Telegram
- `--add-binary ffmpeg.exe`: Incluye FFmpeg para conversión de audio
- `--add-binary browsers.json`: Fix para fake_useragent

### 📍 El ejecutable se genera en: `dist/bot_del_estadio.exe`

---

## 🔧 Para crear nuevo ambiente virtual:

```bash
# Crear entorno
python -m venv bot-env

# Activar (PowerShell)
.\bot-env\Scripts\activate.bat

# Activar (Git Bash)
source bot-env/Scripts/activate

# Actualizar pip
python -m pip install --upgrade pip

# Instalar dependencias
python -m pip install -r requirements.txt

# Listar paquetes instalados
pip list

# Instalar PyInstaller para compilación
pip install -U pyinstaller

# Desactivar entorno
deactivate
```

---

## 🩹 Correcciones Conocidas (si es necesario)

### Steam Web API Version Fix:
**Archivo:** `bot-env/Lib/site-packages/steam_web_api/_version.py`
```python
# Cambiar:
# __version__ = "Unknown"
# Por:
try:
    from ._version import __version__
except ImportError:
    __version__ = "2.0.4"
```

### Fake UserAgent Fix:
**Verificar que existe:** 
```
bot-env\Lib\site-packages\fake_useragent\data\browsers.json
```
*Si no existe, renombrar `browsers.jsonl` a `browsers.json`*

---

## ✅ Verificación de Compilación Exitosa

El bot debería mostrar al iniciar:
```
[INFO] Conexión exitosa a rawg.io.
[INFO] conexión exitosa con Steam.
[INFO] Dólar oficial a: [precio]
[INFO] Obtenida la lista con 50 videos.
[INFO] Bot inicializado correctamente
```

---

## 📊 Información de Build

| Versión | Fecha | Tamaño | Notas |
|---------|-------|--------|-------|
| 270925 | 27/09/2025 | ~113 MB | Refactor completo, nueva estructura |
| 250926 | 26/09/2025 | ~113 MB | Versión anterior |

### 🔗 Dependencias Principales:
- **TwitchIO** - Integración con Twitch
- **RAWG API** - Base de datos de videojuegos  
- **Steam API** - Precios de juegos
- **YouTube API** - Videos del canal
- **FFmpeg** - Conversión de audio para Telegram

---

## 🆘 Troubleshooting

### Problema: "Execution of scripts is disabled"
**Solución:** Usar `.bat` en lugar de `.ps1`
```powershell
.\bot-env\Scripts\activate.bat
```

### Problema: PyInstaller no encuentra módulos
**Solución:** Ejecutar desde el entorno virtual correcto
```powershell
.\bot-env\Scripts\pyinstaller.exe [parámetros]
```

### Problema: Audio no reproduce
**Solución:** Verificar que `storage/*.wav` esté incluido y Windows tenga códecs

---

## 🎯 Notas de Desarrollo

- ✅ **Estructura refactorizada** (Sep 2025)
- ✅ **15 → 12 archivos** de comandos consolidados
- ✅ **utils/** reorganizado con configuración centralizada
- ✅ **telegram_stuff** → **telegram_bot** 
- ✅ **Logging centralizado** reemplazando prints
- ✅ **Import paths** actualizados completamente


