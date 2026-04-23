# Guía de Instalación - BotDelEstadio

## Instalación en una PC nueva

### Lo que necesitás antes de empezar
- El archivo **`installer.exe`** (pedírselo al administrador del bot)
- El archivo **`secretos.py`** (pedírselo al administrador del bot)

### Pasos

1. Ejecutar `installer.exe` con doble clic
2. Elegir la carpeta donde instalar el bot (por defecto: `C:\Users\TuUsuario\BotDelEstadio`)
3. Hacer clic en **Seleccionar** y buscar el archivo `secretos.py`
4. Hacer clic en **Instalar** y esperar — el instalador hace todo solo:
   - Instala Python y Git si no están en la PC
   - Descarga el bot de GitHub
   - Instala las dependencias
   - Copia el archivo de credenciales
   - Crea un acceso directo en el escritorio
5. Al terminar, usar el acceso directo **Bot del Estadio** del escritorio para abrir el bot

> El instalador requiere conexión a internet.

---

## Uso diario

1. Abrir el acceso directo **Bot del Estadio** del escritorio
2. El launcher verifica automáticamente si hay actualizaciones y las instala antes de que puedas iniciar el bot
3. Hacer clic en **Iniciar**

---

## Actualizar el archivo secretos.py

Si cambian las credenciales, reemplazar el archivo manualmente en:
```
[carpeta de instalación]\utils\secretos.py
```

---

## Compilar el installer.exe (solo para el desarrollador)

El `installer.exe` se genera con PyInstaller desde el entorno de desarrollo:

```powershell
pyinstaller --onefile --windowed --name installer installer.py
```

**Fix obligatorio antes de compilar el bot** (no aplica al installer):

Archivo: `bot-env/Lib/site-packages/steam_web_api/_version.py` líneas 18-19

```python
# Cambiar:
except Exception:
    pass

# Por:
except Exception:
    __version__ = "2.0.4"
```
