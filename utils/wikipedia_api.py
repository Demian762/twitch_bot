"""
API de Wikipedia para obtener datos curiosos

Este módulo proporciona funciones para obtener datos curiosos aleatorios
de las plantillas "¿Sabías que...?" de Wikipedia en español.

Author: Demian762
Version: 251013
"""

import requests
import re
from random import randint, choice
from bs4 import BeautifulSoup
from utils.logger import logger


def obtener_datos_wikipedia(numero_plantilla):
    """
    Obtiene los datos curiosos de una plantilla SQ específica de Wikipedia.
    
    Args:
        numero_plantilla (int): Número de la plantilla (1-250+)
    
    Returns:
        list: Lista de strings con los datos curiosos, o lista vacía si hay error
    
    Example:
        >>> datos = obtener_datos_wikipedia(77)
        >>> print(len(datos))  # Debería retornar ~3 datos
        3
    """
    try:
        url = "https://es.wikipedia.org/w/api.php"
        params = {
            "action": "parse",
            "page": f"Plantilla:SQ/{numero_plantilla}",
            "format": "json",
            "prop": "text"
        }
        
        # Wikipedia requiere un User-Agent para identificar el bot
        headers = {
            "User-Agent": "BotDelEstadio/1.0 (Twitch Bot; Python/requests) Contact: twitch.tv/hablemosdepavadaspod"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Verificar si hay error (plantilla no existe)
        if 'error' in data:
            logger.debug(f"Plantilla SQ/{numero_plantilla} no encontrada")
            return []
        
        # Obtener HTML
        html_content = data['parse']['text']['*']
        
        # Parsear con BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        texto = soup.get_text()
        
        # Extraer datos
        lineas = texto.split('\n')
        datos = []
        
        for linea in lineas:
            linea = linea.strip()
            # Los datos empiezan con "..." y terminan con "?"
            if linea.startswith('...') and '?' in linea:
                # Limpiar: remover "..." del inicio
                dato = linea.replace('...', '', 1).strip()
                # Remover referencias numéricas [1], [2], etc.
                dato = re.sub(r'\s*\[\d+\]\s*$', '', dato).strip()
                dato = re.sub(r'\s+\d+\s*$', '', dato).strip()
                
                # Evitar duplicados
                if dato and dato not in datos:
                    datos.append(dato)
        
        logger.debug(f"Plantilla SQ/{numero_plantilla}: {len(datos)} datos obtenidos")
        return datos
        
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout al obtener plantilla SQ/{numero_plantilla}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de red al obtener plantilla SQ/{numero_plantilla}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error inesperado al obtener plantilla SQ/{numero_plantilla}: {e}")
        return []


def obtener_dato_aleatorio(max_intentos=5):
    """
    Obtiene un dato curioso aleatorio de Wikipedia.
    
    Selecciona una plantilla aleatoria de las 250+ disponibles y retorna
    uno de los datos curiosos de esa plantilla. Si la plantilla no existe
    o falla, reintenta con otra plantilla hasta max_intentos.
    
    Args:
        max_intentos (int): Número máximo de intentos si una plantilla falla
    
    Returns:
        str: Dato curioso formateado con "¿Sabías que...?", o mensaje de error
    
    Example:
        >>> dato = obtener_dato_aleatorio()
        >>> print(dato)
        '¿Sabías que las palomas pueden alimentar a sus crías con leche?'
    
    Note:
        NO usar cache local. El bot pierde datos entre ejecuciones.
    """
    for intento in range(max_intentos):
        # Elegir plantilla aleatoria (1-250)
        numero_plantilla = randint(1, 250)
        
        # Obtener datos de esa plantilla
        datos = obtener_datos_wikipedia(numero_plantilla)
        
        if datos:
            # Elegir uno aleatorio de los ~3 datos disponibles
            dato_elegido = choice(datos)
            # Formatear con "¿Sabías que...?"
            logger.info(f"Dato obtenido de plantilla SQ/{numero_plantilla}")
            return f"¿Sabías que {dato_elegido}"
    
    # Si después de max_intentos no se obtuvo nada
    logger.warning("No se pudo obtener dato de Wikipedia después de varios intentos")
    return "No se pudo obtener un dato curioso en este momento. ¡Intenta de nuevo!"
