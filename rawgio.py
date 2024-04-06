from datetime import date, timedelta
import requests

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
        if response.status_code == 200 and len(response.json().get('results')) > 0:
            nombre = response.json().get('results')[0]["name"]
            puntaje = response.json().get('results')[0]["metacritic"]
            fecha = response.json().get('results')[0]["released"]
            tiempo = response.json().get('results')[0]["playtime"]
            return nombre, puntaje, fecha, tiempo
        else:
            return False, False, False, False
        
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
