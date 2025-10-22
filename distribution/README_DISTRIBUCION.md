# 📦 Proceso de Distribución - Bot del Estadio

Documentación interna para crear y distribuir nuevas versiones del bot a usuarios finales.

## 📋 Índice

- [Vista General](#vista-general)
- [Requisitos Previos](#requisitos-previos)
- [Proceso de Distribución](#proceso-de-distribución)
- [Estructura del Paquete](#estructura-del-paquete)
- [Testing](#testing)
- [Distribución a Usuarios](#distribución-a-usuarios)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Vista General

El sistema de distribución permite empaquetar el bot para que usuarios no técnicos puedan:
1. Descomprimir un ZIP
2. Configurar sus credenciales en `config.ini`
3. Ejecutar `INICIAR_BOT.bat`
4. Disfrutar del bot con actualizaciones automáticas desde GitHub

### Flujo de actualización para usuarios

```
Usuario ejecuta INICIAR_BOT.bat
    ↓
Script verifica Git instalado
    ↓
Clone/actualiza desde GitHub master
    ↓
Verifica/instala dependencias si cambiaron
    ↓
Ejecuta el bot
```

---

## ⚙️ Requisitos Previos

### Para crear la distribución:

- **PowerShell** (viene con Windows)
- **Git** instalado y configurado
- Estar en la rama **master** (recomendado)
- Tener **FFmpeg** en la carpeta `ffmpeg/` del proyecto

### Opcional pero recomendado:

- **Python Embedded** en `python-embedded/` (~20MB)
  - Descarga: https://www.python.org/downloads/
  - Buscar "Windows embeddable package (64-bit)"
  - Descomprimir en carpeta `python-embedded/`

---

## 🚀 Proceso de Distribución

### Paso 1: Preparar el código

```bash
# Asegurate de estar en master
git checkout master

# Asegurate de tener los últimos cambios
git pull origin master

# Verificar que no haya cambios sin commitear
git status
```

### Paso 2: Actualizar versión (opcional)

Editar el número de versión en:
- `bot_del_estadio.py` (si tiene constante de versión)
- O pasar como parámetro al script

### Paso 3: Ejecutar script de empaquetado

```powershell
# Desde la raíz del proyecto
cd distribution
.\setup_distribution.ps1 -Version "1.0"
```

O sin parámetro (usa versión por defecto):

```powershell
.\setup_distribution.ps1
```

### Paso 4: Verificar el paquete generado

El script genera: `BotDelEstadio_v1.0.zip` en la raíz del proyecto.

Verificar que contenga:
- ✅ `INICIAR_BOT.bat`
- ✅ `LEEME.txt`
- ✅ `config/config_template.ini`
- ✅ `config/README.md`
- ✅ `ffmpeg/bin/ffmpeg.exe`
- ✅ `logs/` (carpeta vacía)
- ⭕ `python-embedded/` (opcional)

---

## 📂 Estructura del Paquete

```
BotDelEstadio_v1.0.zip
│
├─ INICIAR_BOT.bat              ← Launcher principal
├─ LEEME.txt                    ← Instrucciones para usuarios
│
├─ config/
│  ├─ config_template.ini       ← Plantilla para copiar
│  └─ README.md                 ← Ayuda de configuración
│
├─ ffmpeg/
│  └─ bin/
│     └─ ffmpeg.exe             ← Procesador de audio
│
├─ python-embedded/             ← Python portable (opcional)
│  ├─ python.exe
│  ├─ python311.dll
│  └─ ...
│
└─ logs/                        ← Carpeta para logs (vacía)
```

**Carpetas que NO se incluyen** (se crean automáticamente):
- `bot/` - Se clona desde GitHub
- `bot-env/` - Entorno virtual de Python

---

## 🧪 Testing

### Test 1: Entorno limpio (Recomendado)

```powershell
# Crear carpeta temporal
mkdir C:\Temp\BotTest
cd C:\Temp\BotTest

# Descomprimir el ZIP
Expand-Archive BotDelEstadio_v1.0.zip -DestinationPath .

# Configurar config.ini
cd config
copy config_template.ini config.ini
notepad config.ini  # Completar con credenciales de prueba

# Ejecutar
cd ..
.\INICIAR_BOT.bat
```

### Checklist de testing:

- [ ] El script detecta Git (o muestra mensaje si no está)
- [ ] El script clona el repositorio correctamente
- [ ] Se crea el entorno virtual
- [ ] Se instalan las dependencias
- [ ] El bot arranca sin errores
- [ ] Los logs se ven en la consola
- [ ] La configuración se carga desde `config.ini`
- [ ] FFmpeg funciona (probar comando de audio)

### Test 2: Actualización

Después de la primera ejecución exitosa:

```powershell
# Hacer un cambio en master (ej: agregar un print)
# Volver a ejecutar
.\INICIAR_BOT.bat
```

- [ ] El script detecta y descarga cambios
- [ ] No reinstala dependencias si no cambiaron
- [ ] El bot arranca con los cambios nuevos

---

## 📤 Distribución a Usuarios

### Método 1: Google Drive / Dropbox

1. Subir `BotDelEstadio_v1.0.zip` a la nube
2. Compartir link con permisos de lectura
3. Enviar link + instrucciones del `LEEME.txt`

### Método 2: GitHub Releases (Recomendado)

```bash
# Crear tag y release
git tag -a v1.0 -m "Release v1.0"
git push origin v1.0
```

Luego en GitHub:
1. Ir a "Releases" → "Draft a new release"
2. Seleccionar tag `v1.0`
3. Subir `BotDelEstadio_v1.0.zip` como asset
4. Publicar release
5. Compartir link del release

### Método 3: Directo

Enviar el ZIP por Discord/Telegram/Email.

---

## 🔧 Troubleshooting

### El ZIP es muy grande (>100MB)

**Causa**: Python embebido incluido.

**Soluciones**:
- Opción A: No incluir Python embebido (usuarios lo instalan)
- Opción B: Usar Python Embedded minimal (sin pip, se instala después)
- Opción C: Distribuir en dos archivos (bot + python)

### FFmpeg no se encuentra

**Verificar**:
```powershell
# Desde la raíz del proyecto
Test-Path .\ffmpeg\bin\ffmpeg.exe
```

Si devuelve `False`:
1. Descargar FFmpeg desde https://github.com/BtbN/FFmpeg-Builds/releases
2. Extraer `ffmpeg.exe` a `ffmpeg/bin/`

### Script de PowerShell no ejecuta

**Error**: "cannot be loaded because running scripts is disabled"

**Solución**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Usuarios reportan que no funciona

**Checklist**:
1. ¿Tienen Git instalado?
2. ¿Configuraron `config.ini` correctamente?
3. ¿Tienen conexión a internet?
4. ¿Qué dice la carpeta `bot/logs/`?

---

## 📝 Changelog

Mantener un registro de versiones distribuidas:

### v1.0 - YYYY-MM-DD
- Primera versión de distribución
- Sistema de actualización automática
- Configuración externa
- FFmpeg incluido

---

## 🔮 Mejoras Futuras

Ideas para mejorar el sistema de distribución:

- [ ] Auto-updater para el launcher mismo (no solo el bot)
- [ ] GUI para configuración inicial (wizard)
- [ ] Instalador con Inno Setup
- [ ] Telemetría opcional (crash reports)
- [ ] Sistema de rollback a versión anterior
- [ ] Verificación de integridad (checksums)
- [ ] Notificaciones de actualizaciones disponibles

---

## 📞 Contacto

Para dudas sobre este proceso:
- Revisar este README
- Consultar código de `setup_distribution.ps1`
- Documentación en `LEEME.txt` (para usuarios)
