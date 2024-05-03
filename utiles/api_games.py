from datetime import date, timedelta
import requests
from howlongtobeatpy import HowLongToBeat
from steam import Steam
from utiles.secretos import steam_api_key

class rawg:

    def __init__(self, rawg_url, rawg_key):
        self.url = rawg_url
        self.key = rawg_key
        self.test_connection()

    def test_connection(self):
        response = requests.get(self.url, params=self.key)
        if response.status_code != 200:
            raise Exception(f"Error al conectar con RAWG.io, status code = {response.status_code}")
        else:
            print("Conexión exitosa a rawg.io.")
    
    def info(self, juego: str):
        key_info = self.key
        key_info["search"] = juego
        key_info["search_precise"] = False
        key_info["search_exact"] = False
        url_info = self.url + "games"
        response = requests.get(url_info, params=key_info)

        if response.status_code != 200:
            return 200, False, False
        
        elif  len(response.json().get('results')) > 0:
            nombre = response.json().get('results')[0]["name"]
            puntaje = response.json().get('results')[0]["metacritic"]
            fecha = response.json().get('results')[0]["released"]
            return nombre, puntaje, fecha
        
        else:
            return None, False, False
        
    def lanzamientos(self, limite):
        key_info = self.key
        desde = str((date.today() - timedelta(days=7)).strftime("%Y-%m-%d"))
        hasta = str((date.today() + timedelta(days=30)).strftime("%Y-%m-%d"))
        key_info["dates"] = desde + "," + hasta
        key_info["page_size"] = limite
        url_info = self.url + "games"
        response = requests.get(url_info, params=key_info)
        if response.status_code == 200 and len(response.json().get('results')) > 0:
            c = 0
            output = []
            for i in response.json().get('results'):
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
            return False

def howlong(game_name:str):
    results_list = HowLongToBeat().search(game_name)
    if results_list is not None and len(results_list) > 0:
        best_element = max(results_list, key=lambda element: element.similarity)
        main_story = str(int(best_element.main_story))
        main_extra = str(int(best_element.main_extra))
        completionist = str(int(best_element.completionist))
        tiempo = main_story + " - " + main_extra + " - " + completionist
        return tiempo
    else:
        return False
    
def steam_api():
    try:
        steam = Steam(steam_api_key)
        print("conexión exitosa con Steam.")
        return steam
    except:
        raise "No se pudo conectar a Steam."
    
def steam_price(nombre, steam, dolar):
    try:
        steam_data = steam.apps.search_games(nombre, "AR")['apps'][0]
        precio = float(steam_data['price'].lstrip("$").rstrip(" USD"))
        precio = str(round(precio * dolar, 2))
        nombre_steam = steam_data['name']
        return nombre_steam, precio
    except:
        return False, False