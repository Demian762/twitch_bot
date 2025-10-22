"""
Config Loader - Sistema de configuración externa para BotDelEstadio

Este módulo permite cargar la configuración desde un archivo config.ini externo,
facilitando la distribución del bot sin exponer credenciales en el código.

Prioridad de carga:
1. Archivo config.ini en ../config/config.ini (relativo al bot)
2. Variables de entorno (fallback)
3. Valores por defecto (donde aplique)

Author: Demian762
Version: 1.0
Created: 2025-10-22
"""

import os
import sys
import configparser
from pathlib import Path
from utils.logger import logger

class ConfigLoader:
    """Gestor centralizado de configuración del bot"""
    
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_loaded = False
        self._load_config()
    
    def _get_base_path(self):
        """Determina la ruta base dependiendo de si es ejecutable o script"""
        if getattr(sys, 'frozen', False):
            # Ejecutándose como .exe (PyInstaller)
            # La carpeta config/ debe estar al mismo nivel que el .exe
            return Path(sys.executable).parent
        else:
            # Ejecutándose como script
            # utils/config_loader.py → parent es utils/ → parent.parent es 00_twitch_bot/
            return Path(__file__).parent.parent
    
    def _load_config(self):
        """Carga el archivo config.ini desde la ubicación externa"""
        base_path = self._get_base_path()
        config_path = base_path / 'config' / 'config.ini'
        
        logger.info(f"Buscando configuración en: {config_path}")
        
        if config_path.exists():
            try:
                self.config.read(config_path, encoding='utf-8')
                self.config_loaded = True
                logger.info("Configuracion cargada exitosamente")
            except Exception as e:
                logger.error(f"Error al leer config.ini: {e}")
                logger.warning("Se usaran variables de entorno como fallback")
        else:
            logger.warning(f"No se encontró config.ini en {config_path}")
            logger.warning("Se usarán variables de entorno como fallback")
    
    def get(self, section, key, fallback=None):
        """
        Obtiene un valor de configuración con sistema de fallback
        
        Args:
            section: Sección del archivo INI
            key: Clave a buscar
            fallback: Valor por defecto si no se encuentra
            
        Returns:
            Valor de configuración (primero config.ini, luego env var, luego fallback)
        """
        # Intenta obtener desde config.ini
        if self.config_loaded:
            try:
                value = self.config.get(section, key, raw=True)
                # Si el valor es un placeholder, ignóralo
                if value and not value.startswith('tu_'):
                    return value
            except (configparser.NoSectionError, configparser.NoOptionError):
                pass
        
        # Fallback a variable de entorno
        env_key = f"{section}_{key}".upper()
        env_value = os.getenv(env_key)
        if env_value:
            return env_value
        
        # Fallback final
        if fallback is not None:
            return fallback
        
        # Si llegamos aquí, no se encontró el valor
        logger.warning(f"No se encontró configuración para {section}.{key}")
        return None
    
    def get_int(self, section, key, fallback=None):
        """Obtiene un valor como entero"""
        value = self.get(section, key, fallback)
        try:
            return int(value) if value else fallback
        except (ValueError, TypeError):
            return fallback
    
    def get_gspread_credentials(self):
        """
        Construye el diccionario de credenciales de Google Sheets
        
        Returns:
            dict: Credenciales en formato esperado por gspread
        """
        if not self.config_loaded:
            logger.error("Config no cargada, no se pueden obtener credenciales de gspread")
            return None
        
        try:
            # Obtener private_key con saltos de línea correctos
            private_key = self.get('GOOGLE_SHEETS', 'gspread_private_key', '')
            # Reemplazar \n literales por saltos de línea reales
            private_key = private_key.replace('\\n', '\n')
            
            credentials = {
                "type": self.get('GOOGLE_SHEETS', 'gspread_type'),
                "project_id": self.get('GOOGLE_SHEETS', 'gspread_project_id'),
                "private_key_id": self.get('GOOGLE_SHEETS', 'gspread_private_key_id'),
                "private_key": private_key,
                "client_email": self.get('GOOGLE_SHEETS', 'gspread_client_email'),
                "client_id": self.get('GOOGLE_SHEETS', 'gspread_client_id'),
                "auth_uri": self.get('GOOGLE_SHEETS', 'gspread_auth_uri'),
                "token_uri": self.get('GOOGLE_SHEETS', 'gspread_token_uri'),
                "auth_provider_x509_cert_url": self.get('GOOGLE_SHEETS', 'gspread_auth_provider_cert_url'),
                "client_x509_cert_url": self.get('GOOGLE_SHEETS', 'gspread_client_cert_url'),
                "universe_domain": self.get('GOOGLE_SHEETS', 'gspread_universe_domain')
            }
            
            # Verificar que las credenciales no sean placeholders
            if credentials['client_email'].startswith('tu_'):
                logger.error("Credenciales de Google Sheets no configuradas correctamente")
                return None
            
            return credentials
        except Exception as e:
            logger.error(f"Error al construir credenciales de gspread: {e}")
            return None


# Instancia global del cargador de configuración
config_loader = ConfigLoader()
