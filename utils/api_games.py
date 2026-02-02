from datetime import date, timedelta
import requests
import time
import re
from howlongtobeatpy import HowLongToBeat
from steam_web_api  import Steam
from utils.secretos import steam_api_key
from utils.logger import logger

class rawg:

    def __init__(self, rawg_url, rawg_key):
        self.url = rawg_url
        self.key = rawg_key
        self.test_connection()

    def test_connection(self):
        response = requests.get(self.url, params=self.key)
        if response.status_code != 200:
            logger.error(f"Hubo un problema con la base de datos de RAWG.io, status code = {response.status_code}")
        else:
            logger.info("Conexión exitosa a rawg.io.")
    
    def info(self, juego: str):
        key_info = self.key
        key_info["search"] = juego
        key_info["search_precise"] = False
        key_info["search_exact"] = False
        url_info = self.url + "games"
        for intento in range(3):
            response = requests.get(url_info, params=key_info)
            if response.status_code == 200:
                break
            logger.warning(f"Info API - Intento {intento + 1}/3 falló con status code: {response.status_code}")
            if intento < 2:  # No esperar después del último intento
                time.sleep(2)
        if response.status_code != 200:
            logger.error(f"Hubo un problema con la base de datos de RAWG.io, status code: {response.status_code}")
            return 200, False, False
        
        elif  len(response.json().get('results')) > 0:
            nombre = response.json().get('results')[0]["name"]
            puntaje = response.json().get('results')[0]["metacritic"]
            fecha = response.json().get('results')[0]["released"]
            return nombre, puntaje, fecha
        
        else:
            return None, False, False
        
    def lanzamientos(self, limite):
        key_info = self.key.copy()  # Crear una copia para evitar modificar el original
        desde = str((date.today() - timedelta(days=15)).strftime("%Y-%m-%d"))  # 15 días atrás
        hasta = str((date.today() + timedelta(days=30)).strftime("%Y-%m-%d"))  # 30 días adelante
        key_info["dates"] = desde + "," + hasta
        key_info["page_size"] = limite
        url_info = self.url + "games"
        
        for intento in range(3):
            response = requests.get(url_info, params=key_info)
            if response.status_code == 200:
                break
            logger.warning(f"Lanzamientos API - Intento {intento + 1}/3 falló con status code: {response.status_code}")
            if intento < 2:  # No esperar después del último intento
                time.sleep(2)
        
        logger.info(f"Lanzamientos API - Status: {response.status_code}, Desde: {desde}, Hasta: {hasta}")
        
        if response.status_code == 200:
            results = response.json().get('results', [])
            logger.info(f"Lanzamientos API - Resultados encontrados: {len(results)}")
            
            if len(results) > 0:
                c = 0
                output = []
                for i in results:
                    if c >= limite:
                        break
                    temp = ""
                    temp = temp + i['name'] + " - Para: "
                    for e in i['platforms']:
                        temp = temp + e['platform']['name'] + " "
                    temp = temp + " - Fecha: " + i['released']
                    output.append(temp)
                    c+=1
                return output
            else:
                logger.warning("Lanzamientos API - No se encontraron resultados en el rango de fechas")
                return False
        else:
            logger.error(f"Hubo un problema con la base de datos de RAWG.io: {response.status_code}")
            return False

def howlong(game_name:str):
    for intento in range(3):
        try:
            hltb = HowLongToBeat()
            
            # Verificar que la instancia se creó correctamente
            if hltb is None or not hasattr(hltb, 'search'):
                logger.warning(f"HowLongToBeat API - Intento {intento + 1}/3: Instancia inválida")
                if intento < 2:
                    time.sleep(2)
                continue
            
            results_list = hltb.search(game_name)
            if results_list is not None and len(results_list) > 0:
                best_element = max(results_list, key=lambda element: element.similarity)
                main_story = str(int(best_element.main_story))
                main_extra = str(int(best_element.main_extra))
                completionist = str(int(best_element.completionist))
                tiempo = main_story + " - " + main_extra + " - " + completionist
                logger.info(f"HowLongToBeat API - Tiempo obtenido exitosamente para {game_name}")
                return tiempo
            else:
                logger.info(f"HowLongToBeat API - No se encontraron resultados para {game_name}")
                return False
        except AttributeError as ae:
            logger.warning(f"HowLongToBeat API - Intento {intento + 1}/3 falló (AttributeError): {str(ae)}")
            if intento < 2:
                time.sleep(2)
        except Exception as e:
            logger.warning(f"HowLongToBeat API - Intento {intento + 1}/3 falló: {str(e)}")
            if intento < 2:  # No esperar después del último intento
                time.sleep(2)
    
    logger.error(f"HowLongToBeat API - No se pudo obtener tiempo para {game_name} después de 3 intentos")
    return False
    
def steam_api():
    try:
        steam = Steam(steam_api_key)
        logger.info("conexión exitosa con Steam.")
        return steam
    except:
        raise Exception("No se pudo conectar a Steam.")
    
def steam_price(nombre, steam, dolar):
    for intento in range(3):
        try:
            steam_data = steam.apps.search_games(nombre, "AR")['apps'][0]
            precio = float(steam_data['price'].lstrip("$").rstrip(" USD"))
            precio = str(round(precio * dolar, 2))
            nombre_steam = steam_data['name']
            logger.info(f"Steam API - Precio obtenido exitosamente para {nombre}")
            return nombre_steam, precio
        except Exception as e:
            logger.warning(f"Steam API - Intento {intento + 1}/3 falló: {str(e)}")
            if intento < 2:  # No esperar después del último intento
                time.sleep(2)
    
    logger.error(f"Steam API - No se pudo obtener precio para {nombre} después de 3 intentos")
    return False, False

def steam_requirements(nombre, steam):
    """
    Obtiene los requisitos mínimos y recomendados de un juego desde Steam
    
    Args:
        nombre (str): Nombre del juego
        steam: Instancia de Steam API
        
    Returns:
        tuple: (requisitos_minimos, requisitos_recomendados) como strings,
               o (False, False) si falla
               
    Note:
        Los requisitos vienen en HTML, esta función los parsea y limpia
    """
    for intento in range(3):
        try:
            # Buscar el juego
            steam_data = steam.apps.search_games(nombre, "AR")['apps'][0]
            app_id = steam_data.get('id')
            # La API puede devolver id como lista, normalizar a int
            if isinstance(app_id, list):
                app_id = app_id[0] if app_id else None
            if not app_id:
                logger.warning(f"Steam Requirements - No se encontró app_id para {nombre}")
                return False, False
            
            # Obtener detalles completos del juego con requisitos
            details = steam.apps.get_app_details(app_id, country="AR", filters="basic")
            
            if str(app_id) not in details or not details[str(app_id)]['success']:
                logger.warning(f"Steam Requirements - No se pudieron obtener detalles para {nombre}")
                return False, False
            
            game_data = details[str(app_id)]['data']
            
            # Obtener requisitos de PC
            pc_reqs = game_data.get('pc_requirements', {})
            
            if not pc_reqs or (not pc_reqs.get('minimum') and not pc_reqs.get('recommended')):
                logger.info(f"Steam Requirements - No hay requisitos disponibles para {nombre}")
                return False, False
            
            # Parsear requisitos mínimos
            min_req = pc_reqs.get('minimum', '')
            min_parsed = _parse_requirements(min_req) if min_req else None
            
            # Parsear requisitos recomendados
            rec_req = pc_reqs.get('recommended', '')
            rec_parsed = _parse_requirements(rec_req) if rec_req else None
            
            logger.info(f"Steam Requirements - Requisitos obtenidos exitosamente para {nombre}")
            return min_parsed, rec_parsed
            
        except Exception as e:
            logger.warning(f"Steam Requirements - Intento {intento + 1}/3 falló: {str(e)}")
            if intento < 2:
                time.sleep(2)
    
    logger.error(f"Steam Requirements - No se pudieron obtener requisitos para {nombre} después de 3 intentos")
    return False, False

def _parse_requirements(html_text):
    """
    Parsea HTML de requisitos de Steam y extrae información limpia
    
    Args:
        html_text (str): HTML con requisitos del sistema
        
    Returns:
        str: Requisitos parseados y formateados, o None si falla
    """
    if not html_text:
        return None
    
    try:
        # Eliminar todas las etiquetas HTML
        text = re.sub(r'<[^>]+>', '', html_text)
        
        # Limpiar espacios múltiples y saltos de línea
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Extraer componentes principales usando patrones
        components = {}
        
        # OS
        os_match = re.search(r'OS[:\s]+([^\n]+?)(?:Processor|Memory|Graphics|DirectX|Storage|Network|$)', text, re.IGNORECASE)
        if os_match:
            components['OS'] = os_match.group(1).strip()
        
        # Processor
        proc_match = re.search(r'Processor[:\s]+([^\n]+?)(?:Memory|Graphics|DirectX|Storage|Network|$)', text, re.IGNORECASE)
        if proc_match:
            components['CPU'] = proc_match.group(1).strip()
        
        # Memory
        mem_match = re.search(r'Memory[:\s]+([^\n]+?)(?:Graphics|DirectX|Storage|Hard Disk|Network|$)', text, re.IGNORECASE)
        if mem_match:
            components['RAM'] = mem_match.group(1).strip()
        
        # Graphics
        gpu_match = re.search(r'(?:Graphics|Video Card)[:\s]+([^\n]+?)(?:DirectX|Storage|Hard Disk|Network|Sound|$)', text, re.IGNORECASE)
        if gpu_match:
            components['GPU'] = gpu_match.group(1).strip()
        
        # Storage
        storage_match = re.search(r'(?:Storage|Hard Disk Space)[:\s]+([^\n]+?)(?:DirectX|Network|Sound|Additional|$)', text, re.IGNORECASE)
        if storage_match:
            components['Almacenamiento'] = storage_match.group(1).strip()
        
        # Construir string de salida
        if not components:
            return None
        
        parts = [f"{key}: {value}" for key, value in components.items() if value]
        return " | ".join(parts)
        
    except Exception as e:
        logger.error(f"Error parseando requisitos: {e}")
        return None
