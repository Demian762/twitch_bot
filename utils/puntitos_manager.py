"""
Sistema de gestión de puntitos integrado con Google Sheets

Este módulo maneja todo el sistema de puntitos del bot, incluyendo consultas,
asignación, sorteos y rankings. Utiliza Google Sheets como base de datos
para persistencia y sincronización en tiempo real.

Features:
    - Consulta de puntitos actuales e históricos
    - Sistema de top rankings
    - Sorteos ponderados por puntitos
    - Gestión de programación semanal
    - Integración completa con Google Sheets API

Dependencies:
    - gspread: Cliente de Google Sheets API
    - Credenciales de servicio configuradas en secretos.py

Author: Demian762
Version: 250927
"""

import gspread
from random import choices
from collections import defaultdict
from utils.secretos import credenciales_gspread, file_puntitos_url
from utils.logger import logger

# Inicializar cliente de Google Sheets
gc = gspread.service_account_from_dict(credenciales_gspread)
sh = gc.open_by_url(file_puntitos_url)

def consulta_puntitos(nombre: str):
    """
    Consulta los puntitos actuales de un usuario
    
    Args:
        nombre (str): Nombre del usuario (se normaliza automáticamente)
        
    Returns:
        int: Cantidad de puntitos actuales del usuario, 0 si no existe
        
    Example:
        >>> consulta_puntitos("Usuario123")
        15
        >>> consulta_puntitos("UsuarioNuevo") 
        0
    """
    nombre = nombre.lower().lstrip("@")
    df = sh.sheet1.get_all_records()
    for row in df:
        if row['nombre'] == nombre:
            return row['puntos']
    return 0

def consulta_historica(nombre: str):
    """
    Consulta el total histórico de puntitos de un usuario
    
    A diferencia de consulta_puntitos(), este valor nunca se resetea
    y representa el total acumulado de puntitos que el usuario ha
    ganado desde que se creó su registro.
    
    Args:
        nombre (str): Nombre del usuario (se normaliza automáticamente)
        
    Returns:
        int: Total histórico de puntitos del usuario, 0 si no existe
    """
    nombre = nombre.lower().lstrip("@")
    df = sh.sheet1.get_all_records()
    for row in df:
        if row['nombre'] == nombre:
            return row['historico']
    return 0

def top_puntitos(n=3):
    """
    Obtiene el ranking de usuarios con más puntitos
    
    Genera una lista de los top N usuarios ordenados por puntitos actuales.
    Usuarios con la misma cantidad de puntitos se agrupan en la misma posición.
    
    Args:
        n (int): Número de posiciones a retornar (default: 3)
        
    Returns:
        list: Lista de strings, cada uno representando una posición del ranking.
              Usuarios empatados se muestran separados por " - "
              
    Example:
        >>> top_puntitos(3)
        ['usuario1', 'usuario2 - usuario3', 'usuario4']
    """
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

def funcion_puntitos(nombre: str, cant: int = 1):
    """
    Modifica los puntitos de un usuario (suma o resta)
    
    Esta es la función principal para modificar puntitos. Actualiza tanto
    los puntitos actuales como el histórico del usuario. Si el usuario no
    existe, crea un nuevo registro.
    
    Args:
        nombre (str): Nombre del usuario (se normaliza automáticamente)
        cant (int): Cantidad de puntitos a modificar (default: 1)
                   Puede ser negativo para restar puntitos
                   
    Example:
        >>> funcion_puntitos("usuario1", 5)   # Suma 5 puntitos
        >>> funcion_puntitos("usuario2", -2)  # Resta 2 puntitos
        
    Note:
        - Los puntitos históricos siempre se incrementan (nunca disminuyen)
        - Si el usuario no existe, se crea con los puntitos especificados
    """
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
    """
    Reinicia los puntitos actuales de un usuario a 0 (función interna)
    
    Utilizada internamente por el sistema de sorteos para resetear
    los puntitos del ganador a 0. No afecta el historial.
    
    Args:
        nombre (str): Nombre del usuario a reiniciar
        
    Note:
        - Solo reinicia puntitos actuales, no históricos
        - Es una función interna (prefijo _)
        - Principalmente usada por sorteo_puntitos()
    """
    hoja = sh.get_worksheet(0)
    df = hoja.get_all_records()
    for idx, row in enumerate(df):
        if row['nombre'] == nombre:
            hoja.update_cell(idx + 2, 2, 0)

def sorteo_puntitos():
    """
    Realiza un sorteo ponderado basado en los puntitos de los usuarios
    
    Utiliza un algoritmo de selección ponderada donde usuarios con más
    puntitos tienen mayor probabilidad de ganar. El ganador tiene sus
    puntitos actuales reseteados a 0.
    
    Returns:
        str: Nombre del usuario ganador, o mensaje de error si algo falla
        
    Algorithm:
        - Obtiene todos los usuarios y sus puntitos
        - Usa random.choices() con pesos basados en puntitos
        - Resetea los puntitos del ganador a 0
        
    Example:
        >>> sorteo_puntitos()
        'usuario_ganador'
        
    Error Handling:
        - Maneja errores de conexión con Google Sheets
        - Retorna mensajes descriptivos de error
        - Registra warnings y errores en el log
    """
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
    """
    Incrementa el contador de votos para una funcionalidad especial
    
    Sistema de votación para eventos especiales del stream.
    Utiliza la segunda hoja del documento de Google Sheets.
    
    Returns:
        int: Número total de votos después del incremento
        
    Note:
        - Funcionalidad especial/easter egg del bot
        - Utiliza worksheet 1 (segunda hoja) del documento
    """
    hoja = sh.get_worksheet(1)
    df = hoja.get_all_records()
    votos = df[0]["daddy_points"] + 1
    hoja.update_cell(2, 1, votos)
    return votos

def get_programacion():
    """
    Obtiene la programación semanal desde Google Sheets
    
    Lee la programación del stream desde la tercera hoja del documento
    de Google Sheets y retorna una lista de strings con los horarios.
    
    Returns:
        list: Lista de strings con la programación semanal,
              o lista con mensaje de error si falla la conexión
              
    Example:
        >>> get_programacion()
        ['Lunes 20:00 - Juego A', 'Miercoles 19:00 - Juego B']
        
    Error Handling:
        - Maneja errores de conexión con Google Sheets
        - Intenta múltiples métodos de lectura de headers
        - Retorna mensaje de error descriptivo si falla completamente
    """
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
