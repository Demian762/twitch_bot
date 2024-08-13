import requests
import pandas as pd
from configuracion import puntitos_file_path


def precio_dolar():
    response = requests.get("https://dolarapi.com/v1/dolares/tarjeta")
    if response:
        print("Dólar tarjeta a: " + str(response.json()['venta']))
        return response.json()['venta']
    else:
        print("No se obtuvo el precio del dólar.")
        return 0

def get_args(args):
    respuesta = ""
    for i in args:
        respuesta = respuesta + " " + i
    respuesta = respuesta.strip().lower()
    return respuesta

def funcion_puntitos(nombre:str, cant=1):
    nombre = nombre.lower().lstrip("@")
    df = pd.read_csv(puntitos_file_path)
    if df[df["usuario"] == nombre].shape[0] == 0:
        df = df._append({"usuario":nombre,"puntos":0}, ignore_index=True)
    puntos = df.loc[df[df["usuario"] == nombre].index[0],"puntos"]
    df.loc[df[df["usuario"] == nombre].index[0],"puntos"] = puntos + cant
    df.to_csv(puntitos_file_path, index=False)

def consulta_puntitos(nombre:str):
    nombre = nombre.lower().lstrip("@")
    df = pd.read_csv(puntitos_file_path)
    if df[df["usuario"] == nombre].shape[0] == 0:
        return 0
    else:
        return df[df["usuario"] == nombre]["puntos"].values[0]
    
def top_puntitos():
    df = pd.read_csv(puntitos_file_path)
    df_sorted = df.sort_values(by='puntos', ascending=False).head(3)
    lista = df_sorted['usuario'].tolist()
    return lista