@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

:: ============================================================================
:: BOT DEL ESTADIO - Launcher Script
:: ============================================================================
:: Este script:
:: - Verifica que Git esté instalado
:: - Clona o actualiza el repositorio desde GitHub
:: - Configura el entorno virtual de Python
:: - Instala/actualiza dependencias si es necesario
:: - Ejecuta el bot
:: ============================================================================

color 0A
title Bot del Estadio - Launcher

echo.
echo ================================================================
echo            BOT DEL ESTADIO - INICIANDO
echo ================================================================
echo.

:: Variables de configuración
set "REPO_URL=https://github.com/Demian762/twitch_bot.git"
set "REPO_BRANCH=master"
set "BOT_DIR=bot"
set "VENV_DIR=bot-env"
set "PYTHON_DIR=python-embedded"
set "REQUIREMENTS_HASH_FILE=.requirements_hash"

:: ============================================================================
:: 1. VERIFICAR GIT
:: ============================================================================
echo [1/5] Verificando Git...
git --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo.
    echo ================================================================
    echo   ERROR: Git no esta instalado
    echo ================================================================
    echo.
    echo   Por favor instala Git desde:
    echo   https://git-scm.com/download/win
    echo.
    echo   Es gratis y toma solo 2 minutos.
    echo   Despues de instalarlo, ejecuta este script nuevamente.
    echo.
    echo ================================================================
    echo.
    echo Presiona cualquier tecla para abrir la pagina de descarga...
    pause >nul
    start https://git-scm.com/download/win
    exit /b 1
)
echo    ✓ Git instalado correctamente
echo.

:: ============================================================================
:: 2. CLONAR O ACTUALIZAR REPOSITORIO
:: ============================================================================
echo [2/5] Actualizando código desde GitHub...
echo.

if not exist "%BOT_DIR%\" (
    echo    Primera ejecución: clonando repositorio...
    git clone -b %REPO_BRANCH% %REPO_URL% %BOT_DIR%
    if errorlevel 1 (
        color 0C
        echo.
        echo ERROR: No se pudo clonar el repositorio.
        echo Verifica tu conexión a internet.
        echo.
        pause
        exit /b 1
    )
    echo    ✓ Repositorio clonado exitosamente
) else (
    echo    Actualizando a la última versión...
    cd %BOT_DIR%
    git fetch origin %REPO_BRANCH% >nul 2>&1
    git reset --hard origin/%REPO_BRANCH% >nul 2>&1
    git pull origin %REPO_BRANCH%
    if errorlevel 1 (
        echo    ! Advertencia: No se pudo actualizar ^(continuando con versión actual^)
        cd ..
    ) else (
        echo    ✓ Código actualizado a la última versión
        cd ..
    )
)
echo.

:: ============================================================================
:: 3. CONFIGURAR PYTHON EMBEBIDO Y ENTORNO VIRTUAL
:: ============================================================================
echo [3/5] Configurando Python...

:: Usar Python embebido si existe, sino el del sistema
if exist "%PYTHON_DIR%\python.exe" (
    set "PYTHON_EXE=%CD%\%PYTHON_DIR%\python.exe"
    echo    ✓ Usando Python embebido
) else (
    :: Verificar Python del sistema
    python --version >nul 2>&1
    if errorlevel 1 (
        color 0C
        echo.
        echo ╔═══════════════════════════════════════════════════════════╗
        echo ║  ERROR: Python no está instalado                          ║
        echo ║                                                           ║
        echo ║  Por favor instalá Python desde:                          ║
        echo ║  https://www.python.org/downloads/                        ║
        echo ║                                                           ║
        echo ║  Durante la instalación, marcá:                           ║
        echo ║  [X] Add Python to PATH                                   ║
        echo ╚═══════════════════════════════════════════════════════════╝
        echo.
        pause
        exit /b 1
    )
    set "PYTHON_EXE=python"
    echo    ✓ Usando Python del sistema
)

:: Crear entorno virtual si no existe
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo    Creando entorno virtual...
    %PYTHON_EXE% -m venv %VENV_DIR%
    if errorlevel 1 (
        echo    ! Error al crear entorno virtual, continuando sin él...
        set "USE_VENV=0"
    ) else (
        echo    ✓ Entorno virtual creado
        set "USE_VENV=1"
    )
) else (
    echo    ✓ Entorno virtual encontrado
    set "USE_VENV=1"
)

:: Activar entorno virtual si está disponible
if "%USE_VENV%"=="1" (
    call %VENV_DIR%\Scripts\activate.bat
    set "PYTHON_CMD=python"
) else (
    set "PYTHON_CMD=%PYTHON_EXE%"
)
echo.

:: ============================================================================
:: 4. INSTALAR/ACTUALIZAR DEPENDENCIAS
:: ============================================================================
echo [4/5] Verificando dependencias...

:: Calcular hash del requirements.txt
set "REQUIREMENTS_FILE=%BOT_DIR%\requirements.txt"
if exist "%REQUIREMENTS_FILE%" (
    :: Verificar si necesitamos instalar (primera vez o requirements modificado)
    set "NEEDS_INSTALL=0"
    if not exist "%REQUIREMENTS_HASH_FILE%" (
        set "NEEDS_INSTALL=1"
    ) else (
        :: Comparar fecha de modificación
        for %%R in ("%REQUIREMENTS_FILE%") do set "REQ_DATE=%%~tR"
        for %%H in ("%REQUIREMENTS_HASH_FILE%") do set "HASH_DATE=%%~tH"
        if "!REQ_DATE!" GTR "!HASH_DATE!" (
            set "NEEDS_INSTALL=1"
        )
    )
    
    :: Instalar si es necesario
    if "!NEEDS_INSTALL!"=="1" (
        echo    Instalando/actualizando paquetes Python...
        %PYTHON_CMD% -m pip install --upgrade pip --quiet
        %PYTHON_CMD% -m pip install -r "%REQUIREMENTS_FILE%" --quiet
        if errorlevel 1 (
            echo    ! Advertencia: Algunos paquetes pueden no haberse instalado correctamente
        ) else (
            echo    ✓ Dependencias instaladas/actualizadas
            echo instalado>"%REQUIREMENTS_HASH_FILE%"
        )
    ) else (
        echo    ✓ Dependencias ya actualizadas
    )
) else (
    echo    ! No se encontró requirements.txt
)
echo.

:: ============================================================================
:: 5. VERIFICAR CONFIGURACIÓN
:: ============================================================================
echo [5/6] Verificando configuración...

:: Crear secretos.py si no existe (desde template)
if not exist "%BOT_DIR%\utils\secretos.py" (
    if exist "%BOT_DIR%\utils\secretos_template.py" (
        echo    Creando secretos.py desde template...
        copy "%BOT_DIR%\utils\secretos_template.py" "%BOT_DIR%\utils\secretos.py" >nul
        echo    ✓ secretos.py creado
    )
)

if not exist "%BOT_DIR%\config\config.ini" (
    color 0E
    echo.
    echo ╔═══════════════════════════════════════════════════════════╗
    echo ║  PRIMERA VEZ: Configuración necesaria                     ║
    echo ╚═══════════════════════════════════════════════════════════╝
    echo.
    echo Se detectó que es la primera vez que ejecutás el bot.
    echo Es necesario configurar tus credenciales de Twitch.
    echo.
    echo Se abrirá la carpeta de configuración...
    echo.
    echo PASOS A SEGUIR:
    echo   1. Copiá el archivo 'config_template.ini'
    echo   2. Renombralo a 'config.ini'
    echo   3. Editalo con tus credenciales de Twitch
    echo   4. Guardá los cambios
    echo   5. Volvé a ejecutar este launcher
    echo.
    echo Para más información, consultá el archivo README.md
    echo en la carpeta config/
    echo.
    pause
    start explorer "%BOT_DIR%\config"
    exit /b 1
)

echo    ✓ Configuración encontrada
echo.

:: ============================================================================
:: 6. EJECUTAR EL BOT
:: ============================================================================
echo [6/6] Iniciando Bot del Estadio...
echo.
echo ═══════════════════════════════════════════════════════════
echo.

cd %BOT_DIR%
%PYTHON_CMD% bot_del_estadio.py

:: Capturar código de salida
set "EXIT_CODE=%ERRORLEVEL%"
cd ..

echo.
echo ═══════════════════════════════════════════════════════════
echo.

if %EXIT_CODE% NEQ 0 (
    color 0E
    echo El bot finalizó con errores. Código: %EXIT_CODE%
    echo Revisá los logs en la carpeta bot/logs/ para más información.
    echo.
) else (
    echo Bot cerrado correctamente.
    echo.
)

:: Desactivar entorno virtual si estaba activo
if "%USE_VENV%"=="1" (
    call %VENV_DIR%\Scripts\deactivate.bat 2>nul
)

echo Presiona cualquier tecla para salir...
pause >nul
