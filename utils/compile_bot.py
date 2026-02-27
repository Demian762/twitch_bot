"""
Script de compilación para BotDelEstadio

Actualiza la fecha de compilación en configuracion.py e genera el ejecutable.

Uso:
    python utils/compile_bot.py

Author: Demian762
"""

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def update_build_date():
    """Actualiza BUILD_DATE en configuracion.py con la fecha actual"""
    config_file = Path(__file__).parent / "configuracion.py"
    
    # Obtener fecha actual en formato YYYY-MM-DD
    today = datetime.now().strftime("%Y-%m-%d")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Reemplazar BUILD_DATE con la fecha nueva
    new_content = re.sub(
        r'BUILD_DATE = "[\d\-]+"',
        f'BUILD_DATE = "{today}"',
        content
    )
    
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✓ BUILD_DATE actualizado a: {today}")
    return today

def compile_exe(build_date):
    """Ejecuta PyInstaller con el archivo .spec y renombra el ejecutable"""
    spec_file = Path(__file__).parent.parent / "bot_del_estadio.spec"
    dist_folder = Path(__file__).parent.parent / "dist"
    
    print(f"✓ Compilando con: {spec_file}")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--clean", str(spec_file)],
        cwd=Path(__file__).parent.parent
    )
    
    if result.returncode == 0:
        # Renombrar el ejecutable con la fecha
        original_exe = dist_folder / "bot_del_estadio.exe"
        versioned_exe = dist_folder / f"bot_del_estadio_{build_date}.exe"
        
        if original_exe.exists():
            original_exe.rename(versioned_exe)
            print(f"✓ Ejecutable renombrado a: bot_del_estadio_{build_date}.exe")
            return True, versioned_exe.name
    
    return False, None

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 Compilador de BotDelEstadio")
    print("=" * 60)
    
    try:
        # Paso 1: Actualizar fecha
        build_date = update_build_date()
        
        # Paso 2: Compilar
        print("\n📦 Compilando ejecutable...")
        success, exe_name = compile_exe(build_date)
        
        if success:
            print(f"\n✓ ¡Compilación completada exitosamente!")
            print(f"  Versión: {build_date}")
            print(f"  Ejecutable: dist/{exe_name}")
        else:
            print("\n✗ Error durante la compilación")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
    
    print("=" * 60)
