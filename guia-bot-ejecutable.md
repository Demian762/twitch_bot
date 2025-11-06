# 🤖 Guía de Instalación y Compilación - BotDelEstadio

## 📋 Requisitos Previos
- **Python 3.11+** instalado en el sistema
- **Git** clonado del repositorio
- **Windows** (para reproducción de audio y compilación)

---

## 🏗️ Instalación de dependencias:

### Instalación automática (recomendada)
```bash
pip install -r requirements.txt
```

---

## 🩹 FIX OBLIGATORIO antes de compilar

### Steam Web API Version Fix:
**⚠️ APLICAR ANTES de crear el ejecutable**

**Archivo:** `bot-env/Lib/site-packages/steam_web_api/_version.py`

**Línea 18-19:** Cambiar:
```python
except Exception:
    pass
```

**Por:**
```python
except Exception:
    __version__ = "2.0.4"
```

**Razón:** PyInstaller no puede importar `__version__` dinámicamente, causando error al ejecutar el .exe

---

## 📦 Compilar ejecutable con PyInstaller

### Método 1: Usando archivo .spec (RECOMENDADO)

El archivo `bot_del_estadio.spec` ya incluye todas las configuraciones necesarias:
- Hidden imports para steam_web_api
- Datos de fake_useragent
- FFmpeg binario
- Carpetas storage y telegram_bot

```powershell
cd "D:\02 - practicas Python\00_twitch_bot"
.\bot-env\Scripts\pyinstaller.exe bot_del_estadio.spec --clean
```

### Método 2: Comando directo (alternativo)

```powershell
cd "D:\02 - practicas Python\00_twitch_bot"
.\bot-env\Scripts\pyinstaller.exe --onefile --add-data "storage/*;storage" --add-data "telegram_bot;telegram_bot" --add-binary "D:\02 - practicas Python\00_twitch_bot\ffmpeg\ffmpeg.exe;ffmpeg" --add-data "D:\02 - practicas Python\00_twitch_bot\bot-env\Lib\site-packages\fake_useragent\data;fake_useragent/data" --hidden-import steam_web_api._version --hidden-import steam_web_api bot_del_estadio.py
```

### 📍 El ejecutable se genera en: `dist/bot_del_estadio.exe`

---

## 🔧 Crear nuevo ambiente virtual (si es necesario)

```bash
# Crear entorno
python -m venv bot-env

# Activar (PowerShell)
.\bot-env\Scripts\activate

# Actualizar pip
python -m pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt

# Instalar PyInstaller
pip install pyinstaller

# Desactivar entorno
deactivate
```

---

## 📊 Historial de Versiones

| Versión | Fecha | Tamaño | Notas |
|---------|-------|--------|-------|
| 251106 | 06/11/2025 | ~110 MB | Fix steam_web_api con hiddenimports en .spec |
| 251013 | 13/10/2025 | ~110.5 MB | Bug fixes (margarita, paths, steam_web_api), nuevo audio yamete |
| 250927 | 27/09/2025 | ~113 MB | Refactor completo, nueva estructura |

