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
from datetime import datetime
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

def get_restricciones_escupir():
    """
    Obtiene las restricciones configurables para el comando !escupir desde Google Sheets
    
    Lee las restricciones desde la cuarta hoja del documento de Google Sheets.
    Las restricciones incluyen días de la semana, rangos horarios, y penalizaciones.
    
    Returns:
        list: Lista de diccionarios con las restricciones configuradas.
              Cada restricción tiene: 'dia', 'hora_inicio', 'hora_fin', 'penalizacion', 'mensaje'
              Retorna lista vacía si no hay restricciones o si hay error
              
    Structure:
        [
            {
                'dia': 'Monday',  # Día de la semana en inglés (Monday, Tuesday, etc.) o 'All' para todos
                'hora_inicio': '00:00',  # Hora de inicio en formato HH:MM (24h), vacío si no aplica
                'hora_fin': '23:59',  # Hora de fin en formato HH:MM (24h), vacío si no aplica
                'penalizacion': -1,  # Cantidad de puntitos a descontar (negativo o 0, NUNCA positivo)
                'mensaje': 'Los Lunes no se escupe'  # Mensaje personalizado para mostrar
            }
        ]
        
    Note:
        Las penalizaciones SIEMPRE deben ser negativas o cero. Si se proporciona un número
        positivo, el sistema lo convertirá automáticamente a negativo y registrará un warning.
        
    Example:
        >>> get_restricciones_escupir()
        [
            {'dia': 'Monday', 'hora_inicio': '', 'hora_fin': '', 'penalizacion': -1, 'mensaje': 'Los Lunes no se escupe'},
            {'dia': 'Sunday', 'hora_inicio': '14:00', 'hora_fin': '18:00', 'penalizacion': -2, 'mensaje': 'Siesta dominical!'}
        ]
        
    Error Handling:
        - Maneja errores de conexión con Google Sheets
        - Retorna lista vacía si falla la lectura
        - Valida que las restricciones tengan estructura correcta
    """
    try:
        hoja = sh.get_worksheet(3)
        # Intentar leer las restricciones con headers esperados
        try:
            restricciones_dict = hoja.get_all_records(
                expected_headers=['dia', 'hora_inicio', 'hora_fin', 'penalizacion', 'mensaje']
            )
        except Exception as e:
            logger.warning(f"Error con expected_headers en restricciones_escupir, usando método alternativo: {e}")
            restricciones_dict = hoja.get_all_records()
        
        restricciones = []
        for row in restricciones_dict:
            # Validar que la fila tenga los campos requeridos
            if all(key in row for key in ['dia', 'penalizacion', 'mensaje']):
                # Convertir penalización a int si viene como string
                try:
                    penalizacion = int(row['penalizacion']) if row['penalizacion'] else 0
                except (ValueError, TypeError):
                    penalizacion = 0
                
                # IMPORTANTE: Las restricciones NUNCA suman puntos, solo restan o son neutras
                # Asegurar que la penalización sea <= 0
                if penalizacion > 0:
                    logger.warning(f"Restricción con penalización positiva detectada ({penalizacion}), se convertirá a negativa: -{penalizacion}")
                    penalizacion = -penalizacion
                    
                restriccion = {
                    'dia': str(row['dia']).strip() if row['dia'] else '',
                    'hora_inicio': str(row.get('hora_inicio', '')).strip(),
                    'hora_fin': str(row.get('hora_fin', '')).strip(),
                    'penalizacion': penalizacion,
                    'mensaje': str(row['mensaje']).strip() if row['mensaje'] else ''
                }
                
                # Solo agregar si tiene día y mensaje
                if restriccion['dia'] and restriccion['mensaje']:
                    restricciones.append(restriccion)
        
        logger.info(f"Restricciones de escupir cargadas: {len(restricciones)} reglas")
        return restricciones
        
    except Exception as e:
        logger.error(f"Error en get_restricciones_escupir: {e}")
        return []

def validar_restriccion_escupir(restricciones: list, dia_semana: str):
    """
    Valida si el comando !escupir puede ejecutarse basándose en las restricciones configuradas
    
    Comprueba si la fecha/hora actual coincide con alguna restricción activa.
    Si encuentra una restricción que aplica, retorna la información de penalización.
    
    Args:
        restricciones (list): Lista de restricciones obtenida de get_restricciones_escupir()
        dia_semana (str): Día actual de la semana en inglés (Monday, Tuesday, etc.)
        
    Returns:
        dict or None: Si hay una restricción activa, retorna:
                     {
                         'penalizacion': int,  # Cantidad a penalizar (negativo)
                         'mensaje': str  # Mensaje a mostrar al usuario
                     }
                     Si no hay restricción, retorna None
                     
    Logic:
        - Comprueba si el día actual coincide con alguna restricción
        - Si la restricción tiene horas definidas, valida que la hora actual esté en el rango
        - Si la restricción tiene dia='All', aplica a todos los días
        - Las restricciones se evalúan en orden, retorna la primera que coincida
        
    Example:
        >>> restricciones = [{'dia': 'Monday', 'hora_inicio': '', 'hora_fin': '', 'penalizacion': -1, 'mensaje': 'No se escupe los lunes'}]
        >>> validar_restriccion_escupir(restricciones, 'Monday')
        {'penalizacion': -1, 'mensaje': 'No se escupe los lunes'}
        >>> validar_restriccion_escupir(restricciones, 'Tuesday')
        None
    """
    if not restricciones:
        return None
    
    hora_actual = datetime.now().time()
    
    for restriccion in restricciones:
        # Verificar si el día coincide (o si es 'All' que aplica a todos los días)
        if restriccion['dia'] != 'All' and restriccion['dia'] != dia_semana:
            continue
            
        # Si no tiene restricción horaria, la restricción aplica todo el día
        if not restriccion['hora_inicio'] or not restriccion['hora_fin']:
            return {
                'penalizacion': restriccion['penalizacion'],
                'mensaje': restriccion['mensaje']
            }
        
        # Validar rango horario
        try:
            hora_inicio = datetime.strptime(restriccion['hora_inicio'], '%H:%M').time()
            hora_fin = datetime.strptime(restriccion['hora_fin'], '%H:%M').time()
            
            # Verificar si la hora actual está en el rango
            if hora_inicio <= hora_actual <= hora_fin:
                return {
                    'penalizacion': restriccion['penalizacion'],
                    'mensaje': restriccion['mensaje']
                }
        except ValueError as e:
            logger.warning(f"Error al parsear horas en restricción: {restriccion}. Error: {e}")
            continue
    
    # No hay restricciones activas
    return None

def registrar_victoria_sorteo(nombre: str):
    """
    Registra una victoria en sorteo para un usuario en el spreadsheet
    
    Incrementa en 1 el contador de sorteos ganados por el usuario.
    Si el usuario no existe en la hoja de registros, lo crea con valores iniciales.
    Utiliza la quinta hoja (worksheet 4) del documento de Google Sheets.
    
    Args:
        nombre (str): Nombre del usuario ganador (se normaliza automáticamente)
        
    Returns:
        None
        
    Structure de la hoja:
        - Columna 1: nombre
        - Columna 2: sorteos_ganados
        - Columna 3: torneos_ganados
        - Columna 4: timbas_ganadas
        - Columna 5: margaritas_ganadas
        - Columna 6: escupitajo_record
        
    Example:
        >>> registrar_victoria_sorteo("usuario1")  # Primera victoria en sorteo
        >>> registrar_victoria_sorteo("usuario1")  # Segunda victoria en sorteo
        
    Note:
        - Si el usuario no existe, se crea con: sorteos_ganados=1, torneos_ganados=0, timbas_ganadas=0, margaritas_ganadas=0, escupitajo_record=0
        - Si el usuario existe, solo incrementa sorteos_ganados en 1
        - La hoja debe existir previamente (worksheet 4)
    """
    nombre = nombre.lower().lstrip("@")
    
    try:
        hoja = sh.get_worksheet(4)
        df = hoja.get_all_records()
        
        # Buscar si el usuario ya existe
        for idx, row in enumerate(df):
            if row.get('nombre') == nombre:
                # Usuario existe, incrementar sorteos ganados
                sorteos_actuales = row.get('sorteos_ganados', 0)
                hoja.update_cell(idx + 2, 2, sorteos_actuales + 1)
                logger.info(f"Victoria en sorteo registrada para {nombre}: {sorteos_actuales + 1} sorteos ganados")
                return
        
        # Usuario no existe, crear nuevo registro
        nuevo_registro = [nombre, 1, 0, 0, 0, 0]  # sorteos=1, torneos=0, timbas=0, margaritas=0, escupitajo_record=0
        hoja.append_row(nuevo_registro)
        logger.info(f"Nuevo usuario en registros de victorias: {nombre} con 1 sorteo ganado")
        
    except Exception as e:
        logger.error(f"Error al registrar victoria en sorteo para {nombre}: {e}")

def registrar_victoria_torneo(nombre: str, cant: int = 1):
    """
    Registra una victoria en torneo de escupitajos para un usuario en el spreadsheet
    
    Incrementa o decrementa el contador de torneos ganados por el usuario.
    Si el usuario no existe en la hoja de registros, lo crea con valores iniciales.
    Utiliza la quinta hoja (worksheet 4) del documento de Google Sheets.
    
    Args:
        nombre (str): Nombre del usuario ganador (se normaliza automáticamente)
        cant (int): Cantidad a modificar (default: 1). Puede ser negativo para restar
        
    Returns:
        None
        
    Structure de la hoja:
        - Columna 1: nombre
        - Columna 2: sorteos_ganados
        - Columna 3: torneos_ganados
        - Columna 4: timbas_ganadas
        - Columna 5: margaritas_ganadas
        - Columna 6: escupitajo_record
        
    Example:
        >>> registrar_victoria_torneo("usuario1")  # Suma 1 torneo ganado
        >>> registrar_victoria_torneo("usuario1", cant=-1)  # Resta 1 torneo ganado
        >>> registrar_victoria_torneo("usuario2", cant=1)  # Suma 1 torneo ganado
        
    Note:
        - Si el usuario no existe, se crea con: sorteos_ganados=0, torneos_ganados=cant, timbas_ganadas=0, margaritas_ganadas=0, escupitajo_record=0
        - Si el usuario existe, incrementa/decrementa torneos_ganados en cant
        - Funciona igual que funcion_puntitos() pero para el contador de torneos
        - La hoja debe existir previamente (worksheet 4)
    """
    nombre = nombre.lower().lstrip("@")
    
    try:
        hoja = sh.get_worksheet(4)
        df = hoja.get_all_records()
        
        # Buscar si el usuario ya existe
        for idx, row in enumerate(df):
            if row.get('nombre') == nombre:
                # Usuario existe, modificar torneos ganados
                torneos_actuales = row.get('torneos_ganados', 0)
                nuevos_torneos = torneos_actuales + cant
                hoja.update_cell(idx + 2, 3, nuevos_torneos)
                logger.info(f"Victoria en torneo {'sumada' if cant > 0 else 'restada'} para {nombre}: {nuevos_torneos} torneos ganados")
                return
        
        # Usuario no existe, crear nuevo registro
        nuevo_registro = [nombre, 0, cant, 0, 0, 0]  # sorteos=0, torneos=cant, timbas=0, margaritas=0, escupitajo_record=0
        hoja.append_row(nuevo_registro)
        logger.info(f"Nuevo usuario en registros de victorias: {nombre} con {cant} torneo(s) ganado(s)")
        
    except Exception as e:
        logger.error(f"Error al registrar victoria en torneo para {nombre}: {e}")

def consulta_victorias(nombre: str):
    """
    Consulta las victorias (sorteos, torneos, timbas, margaritas) y récord de escupitajo de un usuario
    
    Retorna un diccionario con la cantidad de sorteos, torneos, timbas, margaritas ganadas
    y el récord de escupitajo del usuario desde la hoja de registros de victorias.
    
    Args:
        nombre (str): Nombre del usuario (se normaliza automáticamente)
        
    Returns:
        dict: Diccionario con 'sorteos_ganados', 'torneos_ganados', 'timbas_ganadas', 'margaritas_ganadas' y 'escupitajo_record'
              Retorna todos los valores en 0 si no existe
        
    Example:
        >>> consulta_victorias("usuario1")
        {'sorteos_ganados': 3, 'torneos_ganados': 5, 'timbas_ganadas': 2, 'margaritas_ganadas': 4, 'escupitajo_record': 450}
        >>> consulta_victorias("usuario_nuevo")
        {'sorteos_ganados': 0, 'torneos_ganados': 0, 'timbas_ganadas': 0, 'margaritas_ganadas': 0, 'escupitajo_record': 0}
    """
    nombre = nombre.lower().lstrip("@")
    
    try:
        hoja = sh.get_worksheet(4)
        df = hoja.get_all_records()
        
        for row in df:
            if row.get('nombre') == nombre:
                # Convertir todos los valores a int ya que pueden venir como string del spreadsheet
                return {
                    'sorteos_ganados': int(row.get('sorteos_ganados', 0) or 0),
                    'torneos_ganados': int(row.get('torneos_ganados', 0) or 0),
                    'timbas_ganadas': int(row.get('timbas_ganadas', 0) or 0),
                    'margaritas_ganadas': int(row.get('margaritas_ganadas', 0) or 0),
                    'escupitajo_record': int(row.get('escupitajo_record', 0) or 0)
                }
        
        # Usuario no existe, retornar ceros
        return {
            'sorteos_ganados': 0, 
            'torneos_ganados': 0,
            'timbas_ganadas': 0,
            'margaritas_ganadas': 0,
            'escupitajo_record': 0
        }
        
    except Exception as e:
        logger.error(f"Error al consultar victorias para {nombre}: {e}")
        return {
            'sorteos_ganados': 0, 
            'torneos_ganados': 0,
            'timbas_ganadas': 0,
            'margaritas_ganadas': 0,
            'escupitajo_record': 0
        }

def registrar_victoria_timba(nombre: str):
    """
    Registra una victoria en timba para un usuario en el spreadsheet
    
    Incrementa en 1 el contador de timbas ganadas por el usuario.
    Si el usuario no existe en la hoja de registros, lo crea con valores iniciales.
    Utiliza la quinta hoja (worksheet 4) del documento de Google Sheets.
    
    Args:
        nombre (str): Nombre del usuario ganador (se normaliza automáticamente)
        
    Returns:
        None
        
    Structure de la hoja:
        - Columna 1: nombre
        - Columna 2: sorteos_ganados
        - Columna 3: torneos_ganados
        - Columna 4: timbas_ganadas
        - Columna 5: margaritas_ganadas
        - Columna 6: escupitajo_record
        
    Example:
        >>> registrar_victoria_timba("usuario1")  # Primera victoria en timba
        >>> registrar_victoria_timba("usuario1")  # Segunda victoria en timba
        
    Note:
        - Si el usuario no existe, se crea con: sorteos_ganados=0, torneos_ganados=0, timbas_ganadas=1, margaritas_ganadas=0, escupitajo_record=0
        - Si el usuario existe, solo incrementa timbas_ganadas en 1
        - La hoja debe existir previamente (worksheet 4)
    """
    nombre = nombre.lower().lstrip("@")
    
    try:
        hoja = sh.get_worksheet(4)
        df = hoja.get_all_records()
        
        # Buscar si el usuario ya existe
        for idx, row in enumerate(df):
            if row.get('nombre') == nombre:
                # Usuario existe, incrementar timbas ganadas
                timbas_actuales = int(row.get('timbas_ganadas', 0) or 0)
                hoja.update_cell(idx + 2, 4, timbas_actuales + 1)
                logger.info(f"Victoria en timba registrada para {nombre}: {timbas_actuales + 1} timbas ganadas")
                return
        
        # Usuario no existe, crear nuevo registro
        nuevo_registro = [nombre, 0, 0, 1, 0, 0]  # sorteos=0, torneos=0, timbas=1, margaritas=0, escupitajo_record=0
        hoja.append_row(nuevo_registro)
        logger.info(f"Nuevo usuario en registros de victorias: {nombre} con 1 timba ganada")
        
    except Exception as e:
        logger.error(f"Error al registrar victoria en timba para {nombre}: {e}")

def registrar_victoria_margarita(nombre: str):
    """
    Registra una victoria en margarita para un usuario en el spreadsheet
    
    Incrementa en 1 el contador de margaritas ganadas por el usuario.
    Si el usuario no existe en la hoja de registros, lo crea con valores iniciales.
    Utiliza la quinta hoja (worksheet 4) del documento de Google Sheets.
    
    Args:
        nombre (str): Nombre del usuario ganador (se normaliza automáticamente)
        
    Returns:
        None
        
    Structure de la hoja:
        - Columna 1: nombre
        - Columna 2: sorteos_ganados
        - Columna 3: torneos_ganados
        - Columna 4: timbas_ganadas
        - Columna 5: margaritas_ganadas
        - Columna 6: escupitajo_record
        
    Example:
        >>> registrar_victoria_margarita("usuario1")  # Primera victoria en margarita
        >>> registrar_victoria_margarita("usuario1")  # Segunda victoria en margarita
        
    Note:
        - Si el usuario no existe, se crea con: sorteos_ganados=0, torneos_ganados=0, timbas_ganadas=0, margaritas_ganadas=1, escupitajo_record=0
        - Si el usuario existe, solo incrementa margaritas_ganadas en 1
        - La hoja debe existir previamente (worksheet 4)
    """
    nombre = nombre.lower().lstrip("@")
    
    try:
        hoja = sh.get_worksheet(4)
        df = hoja.get_all_records()
        
        # Buscar si el usuario ya existe
        for idx, row in enumerate(df):
            if row.get('nombre') == nombre:
                # Usuario existe, incrementar margaritas ganadas
                margaritas_actuales = row.get('margaritas_ganadas', 0)
                hoja.update_cell(idx + 2, 5, margaritas_actuales + 1)
                logger.info(f"Victoria en margarita registrada para {nombre}: {margaritas_actuales + 1} margaritas ganadas")
                return
        
        # Usuario no existe, crear nuevo registro
        nuevo_registro = [nombre, 0, 0, 0, 1, 0]  # sorteos=0, torneos=0, timbas=0, margaritas=1, escupitajo_record=0
        hoja.append_row(nuevo_registro)
        logger.info(f"Nuevo usuario en registros de victorias: {nombre} con 1 margarita ganada")
        
    except Exception as e:
        logger.error(f"Error al registrar victoria en margarita para {nombre}: {e}")

def registrar_record_escupitajo(nombre: str, distancia: int):
    """
    Registra o actualiza el récord de escupitajo de un usuario en el spreadsheet
    
    Solo actualiza el récord si la nueva distancia es mayor que la registrada.
    Si el usuario no existe en la hoja de registros, lo crea con valores iniciales.
    Utiliza la quinta hoja (worksheet 4) del documento de Google Sheets.
    
    Args:
        nombre (str): Nombre del usuario (se normaliza automáticamente)
        distancia (int): Distancia del escupitajo en centímetros
        
    Returns:
        bool: True si se actualizó el récord, False si no
        
    Structure de la hoja:
        - Columna 1: nombre
        - Columna 2: sorteos_ganados
        - Columna 3: torneos_ganados
        - Columna 4: timbas_ganadas
        - Columna 5: margaritas_ganadas
        - Columna 6: escupitajo_record
        
    Example:
        >>> registrar_record_escupitajo("usuario1", 150)  # Primer escupitajo, se guarda
        True
        >>> registrar_record_escupitajo("usuario1", 120)  # Menor que el récord, no se actualiza
        False
        >>> registrar_record_escupitajo("usuario1", 200)  # Nuevo récord!
        True
        
    Note:
        - Si el usuario no existe, se crea con: sorteos=0, torneos=0, timbas=0, margaritas=0, escupitajo_record=distancia
        - Si el usuario existe, solo actualiza si la nueva distancia es mayor
        - La hoja debe existir previamente (worksheet 4)
    """
    nombre = nombre.lower().lstrip("@")
    
    try:
        hoja = sh.get_worksheet(4)
        df = hoja.get_all_records()
        
        # Buscar si el usuario ya existe
        for idx, row in enumerate(df):
            if row.get('nombre') == nombre:
                # Usuario existe, verificar si es un nuevo récord
                record_actual = int(row.get('escupitajo_record', 0) or 0)
                
                if distancia > record_actual:
                    hoja.update_cell(idx + 2, 6, distancia)
                    logger.info(f"Nuevo récord de escupitajo para {nombre}: {distancia} cm (anterior: {record_actual} cm)")
                    return True
                else:
                    logger.debug(f"Escupitajo de {nombre} ({distancia} cm) no supera su récord ({record_actual} cm)")
                    return False
        
        # Usuario no existe, crear nuevo registro con este escupitajo como récord
        nuevo_registro = [nombre, 0, 0, 0, 0, distancia]  # sorteos=0, torneos=0, timbas=0, margaritas=0, escupitajo_record=distancia
        hoja.append_row(nuevo_registro)
        logger.info(f"Nuevo usuario en registros de victorias: {nombre} con récord de escupitajo de {distancia} cm")
        return True
        
    except Exception as e:
        logger.error(f"Error al registrar récord de escupitajo para {nombre}: {e}")
        return False

def top_records_escupitajo(n: int = 3):
    """
    Obtiene el ranking de los mejores récords de escupitajo
    
    Retorna una lista con los top N usuarios con los mejores récords de escupitajo,
    ordenados de mayor a menor distancia.
    
    Args:
        n (int): Número de posiciones a retornar (default: 3)
        
    Returns:
        list: Lista de tuplas (nombre, distancia) con los top N récords.
              Retorna lista vacía si no hay récords o si hay error.
              
    Example:
        >>> top_records_escupitajo(3)
        [('usuario1', 480), ('usuario2', 450), ('usuario3', 420)]
        >>> top_records_escupitajo(5)
        [('juan', 500), ('pedro', 475), ('maria', 460), ('ana', 440), ('luis', 430)]
        
    Note:
        - Solo incluye usuarios con récords > 0
        - Ordena de mayor a menor distancia
        - Si hay menos de N usuarios con récords, retorna todos los disponibles
    """
    try:
        hoja = sh.get_worksheet(4)
        df = hoja.get_all_records()
        
        # Filtrar solo usuarios con récords > 0 y convertir a tuplas (nombre, distancia)
        records = []
        for row in df:
            nombre = row.get('nombre')
            record = int(row.get('escupitajo_record', 0) or 0)
            if nombre and record > 0:
                records.append((nombre, record))
        
        # Ordenar por distancia descendente
        records.sort(key=lambda x: x[1], reverse=True)
        
        # Retornar top N
        return records[:n]
        
    except Exception as e:
        logger.error(f"Error al obtener top récords de escupitajo: {e}")
        return []


