import requests

class rawg:

    def __init__(self, rawg_url, rawg_key):
        self.url = rawg_url
        self.key = rawg_key
        self.last_status_code = 0
        self.test_connection()
        self.lista_titulos = []

    def test_connection(self):
        response = requests.get(self.url, params=self.key)
        self.last_status_code = response.status_code
        if response.status_code != 200:
            raise Exception(f"Error al conectar con RAWG.io, status code = {response.status_code}")
        else:
            print("Conexión exitosa a rawg.io.")
    
    def info(self, juego: str):
        key_info = self.key
        key_info["search"] = juego
        url_info = self.url + "games"
        response = requests.get(url_info, params=key_info)
        self.last_status_code = response.status_code
        if response.status_code == 200 and len(response.json().get('results')) > 0:

            nombre = response.json().get('results')[0]["name"]
            puntaje = response.json().get('results')[0]["metacritic"]
            return nombre, puntaje
        else:
            return False, False


