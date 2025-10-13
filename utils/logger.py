"""
Sistema de logging centralizado para el BotDelEstadio

Este módulo configura y proporciona un sistema de logging optimizado para el bot,
con separación de logs del bot de logs de librerías externas y configuración
automática de archivos de log por fecha.

Features:
    - Logs diarios automáticos en carpeta logs/
    - Logger específico para el bot (nivel INFO)
    - Supresión de logs innecesarios de librerías externas
    - Salida tanto a archivo como consola
    - Formato consistente con timestamps

Author: Demian762
Version: 250927
"""

import logging
import os
from datetime import datetime

def setup_logger():
    """
    Configura y retorna el logger principal del bot
    
    Crea un sistema de logging con dos niveles:
    1. Root logger (WARNING) para librerías externas
    2. Bot logger (INFO) para eventos del bot
    
    El sistema automáticamente:
    - Crea la carpeta logs/ si no existe
    - Genera archivos de log diarios (bot_YYYYMMDD.log)
    - Configura formato consistente para todos los logs
    - Silencia logs verbosos de librerías específicas
    
    Returns:
        logging.Logger: Logger configurado para el bot
        
    Example:
        >>> logger = setup_logger()
        >>> logger.info("Bot iniciado correctamente")
    """
    # Crear directorio de logs si no existe
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    # Generar nombre de archivo con fecha actual
    log_file = f"logs/bot_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Configurar el root logger para librerías externas con nivel WARNING
    logging.basicConfig(
        level=logging.WARNING,  # Solo mostrar warnings y errores de librerías externas
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Crear logger específico para el bot con nivel INFO
    bot_logger = logging.getLogger('BotLogger')
    bot_logger.setLevel(logging.INFO)
    
    # Silenciar logs específicos que generan ruido
    logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
    logging.getLogger('oauth2client').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('twitchio').setLevel(logging.WARNING)
    logging.getLogger('steam_web_api').setLevel(logging.WARNING)
    
    return bot_logger

# Instancia global del logger para uso en todo el bot
logger = setup_logger()
