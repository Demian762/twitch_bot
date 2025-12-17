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

### Script Automático

El script `utils/compile_bot.py` automatiza todo el proceso:
1. Actualiza la fecha de compilación en `configuracion.py`
2. Ejecuta PyInstaller con todas las configuraciones

```powershell
cd "D:\02 - practicas Python\00_twitch_bot"
python utils/compile_bot.py
```

**Resultado:**
- Variable `BUILD_DATE` actualizada con formato YYYY-MM-DD
- Ejecutable generado en: `dist/bot_del_estadio.exe`
- Fecha de compilación visible en logs y comando `!version`

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

