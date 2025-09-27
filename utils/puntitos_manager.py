import gspread
from random import choices
from collections import defaultdict
from utils.secretos import credenciales_gspread, file_puntitos_url
from utils.logger import logger


gc = gspread.service_account_from_dict(credenciales_gspread)
sh = gc.open_by_url(file_puntitos_url)

def consulta_puntitos(nombre:str):
    nombre = nombre.lower().lstrip("@")
    df = sh.sheet1.get_all_records()
    for row in df:
        if row['nombre'] == nombre:
            return row['puntos']
    return 0

def consulta_historica(nombre:str):
    nombre = nombre.lower().lstrip("@")
    df = sh.sheet1.get_all_records()
    for row in df:
        if row['nombre'] == nombre:
            return row['historico']
    return 0

def top_puntitos(n=3):
    df = sh.sheet1.get_all_records()
    points_dict = defaultdict(list)
    for row in df:
        points_dict[row['puntos']].append(row['nombre'])

    sorted_points = sorted(points_dict.keys(), reverse=True)

    top_n_names = []
    for points in sorted_points:
        combined_names = " - ".join(points_dict[points])
        top_n_names.append(combined_names)
        if len(top_n_names) >= n:
            break

    return top_n_names[:n]

def funcion_puntitos(nombre:str, cant: int=1):
    nombre = nombre.lower().lstrip("@")
    hoja = sh.get_worksheet(0)
    df = hoja.get_all_records()
    
    for idx, row in enumerate(df):
        if row['nombre'] == nombre:
            puntitos = row['puntos'] + cant
            historicos = row['historico'] + cant
            hoja.update_cell(idx + 2, 2, puntitos)
            hoja.update_cell(idx + 2, 3, historicos)
            return
    nuevo_nombre = [nombre, cant, cant]
    hoja.append_row(nuevo_nombre)

def _reiniciar_puntitos(nombre):
    hoja = sh.get_worksheet(0)
    df = hoja.get_all_records()
    for idx, row in enumerate(df):
        if row['nombre'] == nombre:
            hoja.update_cell(idx + 2, 2, 0)

def sorteo_puntitos():
    try:
        # Intentar con headers esperados
        df = sh.sheet1.get_all_records(expected_headers=['nombre', 'puntos'])
    except Exception as e:
        logger.warning(f"Error con expected_headers, usando método alternativo: {e}")
        # Si falla, intentar sin expected_headers pero manejando el error
        try:
            df = sh.sheet1.get_all_records()
        except Exception as e2:
            logger.error(f"Error en sorteo_puntitos: {e2}")
            # Como fallback, devolver un ganador por defecto
            return "Error en sorteo"
    
    if not df:
        logger.warning("No hay datos para el sorteo")
        return "No hay participantes"
    
    nombres = [row['nombre'] for row in df if 'nombre' in row and 'puntos' in row]
    puntos = [row['puntos'] for row in df if 'nombre' in row and 'puntos' in row]
    
    if not nombres or not puntos:
        logger.warning("No se encontraron datos válidos para el sorteo")
        return "Datos inválidos para sorteo"
    
    ganador = choices(nombres, weights=puntos, k=1)[0]
    _reiniciar_puntitos(ganador)
    return ganador

def daddy_point():
    hoja = sh.get_worksheet(1)
    df = hoja.get_all_records()
    votos = df[0]["daddy_points"] + 1
    hoja.update_cell(2, 1, votos)
    return votos

def get_programacion():
    try:
        hoja = sh.get_worksheet(2)
        # Intentar con headers esperados
        try:
            programacion_dict = hoja.get_all_records(expected_headers=['programacion'])
        except Exception as e:
            logger.warning(f"Error con expected_headers en programacion, usando método alternativo: {e}")
            programacion_dict = hoja.get_all_records()
        
        lista = []
        for i in programacion_dict:
            if 'programacion' in i:
                lista.append(i['programacion'])
        return lista if lista else ["Error: No se pudo cargar la programación"]
    except Exception as e:
        logger.error(f"Error en get_programacion: {e}")
        return ["Error: No se pudo acceder a la programación"]
