import logging
import os
from datetime import datetime

def setup_logger():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
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
    
    return bot_logger

logger = setup_logger()
