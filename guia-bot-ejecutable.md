# 🤖 Guía de Instalación y Compilación - BotDelEstadio

## 📋 Requisitos Previos
- **Python 3.11+** instalado en el sistema
- **Git** p| Versión | Fecha | Tamaño | Notas |
|---------|-------|-----------|-------|
| 250927 | 27/09/2025 | ~113 MB | Refactor completo, nueva estructura | clonado del repositorio
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

#### Comando para PowerShell (Windows):
```powershell
cd "D:\02 - practicas Python\00_twitch_bot"
.\bot-env\Scripts\pyinstaller.exe --onefile --add-data "storage/*;storage" --add-data "telegram_bot;telegram_bot" --add-binary "D:\02 - practicas Python\00_twitch_bot\ffmpeg\ffmpeg.exe;ffmpeg" --add-data "D:\02 - practicas Python\00_twitch_bot\bot-env\Lib\site-packages\fake_useragent\data;fake_useragent/data" bot_del_estadio.py
```

#### Comando para Git Bash (alternativo):
```bash
cd "/d/02 - practicas Python/00_twitch_bot"
./bot-env/Scripts/pyinstaller.exe --onefile --add-data "storage/*:storage" --add-data "telegram_bot:telegram_bot" --add-binary "./ffmpeg/ffmpeg.exe:ffmpeg" --add-data "./bot-env/Lib/site-packages/fake_useragent/data:fake_useragent/data" bot_del_estadio.py
```

#### Parámetros explicados:
- `--onefile`: Crea un solo archivo ejecutable
- `--add-data "storage/*;storage"`: Incluye archivos de audio
- `--add-data "telegram_bot;telegram_bot"`: Incluye módulo de Telegram
- `--add-binary ffmpeg.exe`: Incluye FFmpeg para conversión de audio
- `--add-data fake_useragent/data`: Incluye directorio completo de datos para HowLongToBeat

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
**⚠️ IMPORTANTE:** Aplicar este fix ANTES de compilar con PyInstaller

**Archivo:** `bot-env/Lib/site-packages/steam_web_api/_version.py`
```python
# Cambiar la línea:
except Exception:
    pass

# Por:
except Exception:
    __version__ = "2.0.4"
```

**Razón:** PyInstaller no puede importar `__version__` dinámicamente, causando:
```
ImportError: cannot import name '__version__' from 'steam_web_api._version'
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
| 251013 | 13/10/2025 | ~110.5 MB | Bug fixes (margarita, paths, steam_web_api), nuevo audio yamete |
| 250927 | 27/09/2025 | ~113 MB | Refactor completo, nueva estructura |
| 250926 | 26/09/2025 | ~113 MB | Versión anterior |

### 🔗 Dependencias Principales:
- **TwitchIO** - Integración con Twitch
- **RAWG API** - Base de datos de videojuegos  
- **Steam API** - Precios de juegos
- **YouTube API** - Videos del canal
- **FFmpeg** - Conversión de audio para Telegram

---

##  Notas de Desarrollo

- ✅ **Estructura refactorizada** (Sep 2025)
- ✅ **15 → 12 archivos** de comandos consolidados
- ✅ **utils/** reorganizado con configuración centralizada
- ✅ **telegram_stuff** → **telegram_bot** 
- ✅ **Logging centralizado** reemplazando prints
- ✅ **Import paths** actualizados completamente


