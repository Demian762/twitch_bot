"""
Sistema de gestión de puntitos integrado con Cloudflare D1

Este módulo maneja todo el sistema de puntitos del bot, incluyendo consultas,
asignación, sorteos y rankings. Los datos viven en una base D1 de Cloudflare,
accedida vía el Worker HTTP en cloudflare/worker/ (ver utils/d1_client.py).

Features:
    - Consulta de puntitos actuales e históricos
    - Sistema de top rankings
    - Sorteos ponderados por puntitos
    - Gestión de programación semanal
    - Integración completa con el Worker de Cloudflare D1

Dependencies:
    - requests: cliente HTTP hacia el Worker (ver utils/d1_client.py)
    - d1_worker_url / d1_worker_token configurados en secretos.py

Author: Demian762
Version: 260814 (migración Google Sheets → Cloudflare D1)
"""

from random import choices
from collections import defaultdict
from datetime import datetime

from utils import d1_client
from utils.configuracion import admins
from utils.logger import logger

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
    df = d1_client.get_puntitos_all()
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
    df = d1_client.get_puntitos_all()
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
    df = d1_client.get_puntitos_all()
    points_dict = defaultdict(list)
    for row in df:
        points_dict[row['puntos']].append(row['nombre'])

    sorted_points = sorted(points_dict.keys(), reverse=True)

    top_n_names = []
    for points in sorted_points:
        combined_names = " - ".join(points_dict[points])
        top_n_names.append(f"{combined_names} ({points} pts)")
        if len(top_n_names) >= n:
            break

    return top_n_names[:n]

def posicion_ranking(username: str) -> dict | None:
    """
    Retorna la posición del usuario en el ranking de puntitos actuales e históricos.

    Returns:
        dict con 'puntos', 'historico', 'posicion_actual', 'posicion_historica', 'total_jugadores'
        None si el usuario no existe en el sheet.
    """
    username = username.lower().lstrip("@")
    try:
        df = d1_client.get_puntitos_all()
        if not df:
            return None

        user_row = next((r for r in df if str(r.get('nombre', '')).lower() == username), None)
        if user_row is None:
            return None

        sorted_actual = sorted(df, key=lambda r: r.get('puntos', 0), reverse=True)
        sorted_historico = sorted(df, key=lambda r: r.get('historico', 0), reverse=True)

        pos_actual = next((i + 1 for i, r in enumerate(sorted_actual) if str(r.get('nombre', '')).lower() == username), None)
        pos_historica = next((i + 1 for i, r in enumerate(sorted_historico) if str(r.get('nombre', '')).lower() == username), None)

        return {
            'puntos': user_row.get('puntos', 0),
            'historico': user_row.get('historico', 0),
            'posicion_actual': pos_actual,
            'posicion_historica': pos_historica,
            'total_jugadores': len(df),
        }
    except Exception as e:
        logger.error(f"Error en posicion_ranking para {username}: {e}")
        return None


def validar_puntitos_admin(receptor: str, donante: str = None) -> tuple[bool, str]:
    """
    Valida si se pueden dar puntitos según las reglas actuales

    Reglas:
    - Un admin no puede darse puntitos a sí mismo
    - En general, un admin puede dar puntitos a no-admins y a otros admins
    - Un no-admin puede dar puntitos a admins, pero no a no-admins
    - Como excepción, el admin "hablemosdepavadaspod" no puede dar puntitos a ningún admin

    Args:
        receptor (str): Usuario que recibirá los puntitos
        donante (str, optional): Usuario que da los puntitos. Si es None, no se valida.

    Returns:
        tuple[bool, str]: (puede_dar, mensaje_error)
                         - puede_dar: True si se permite, False si se bloquea
                         - mensaje_error: Mensaje descriptivo si se bloquea, "" si se permite
    """
    # Si no hay donante especificado, permitir (para casos automáticos del bot)
    if donante is None:
        return (True, "")

    receptor_lower = receptor.lower().lstrip("@")
    donante_lower = donante.lower().lstrip("@")
    es_receptor_admin = receptor_lower in admins
    es_donante_admin = donante_lower in admins

    # Ningún usuario puede darse puntitos a sí mismo
    if receptor_lower == donante_lower:
        return (False, "No podés darte puntitos a vos mismo")

    # El admin hablemosdepavadaspod no puede dar puntitos a admins
    if donante_lower == "hablemosdepavadaspod" and es_receptor_admin:
        return (False, "@hablemosdepavadaspod no puede dar puntitos a otros admins")

    # Un no-admin no puede dar puntitos a no-admins
    if not es_donante_admin and not es_receptor_admin:
        return (False, "Los no-admins solo pueden dar puntitos a admins")

    return (True, "")

_bot_state = None

def set_bot_state(state) -> None:
    global _bot_state
    _bot_state = state

def funcion_puntitos(nombre: str, cant: int = 1, donante: str = None):
    """
    Modifica los puntitos de un usuario (suma o resta)

    Esta es la función principal para modificar puntitos. Actualiza tanto
    los puntitos actuales como el histórico del usuario. Si el usuario no
    existe, crea un nuevo registro.

    IMPORTANTE - Reglas de validación de admins:
    - Ningún usuario puede darse puntitos a sí mismo
    - El admin "hablemosdepavadaspod" NO puede dar puntitos a otros admins
    - Los demás admins SÍ pueden dar puntitos a otros admins
    - Un no-admin puede dar puntitos a admins, pero NO a otros no-admins
    - Los admins pueden dar puntitos a no-admins sin restricciones

    Args:
        nombre (str): Nombre del usuario (se normaliza automáticamente)
        cant (int): Cantidad de puntitos a modificar (default: 1)
                   Puede ser negativo para restar puntitos
        donante (str, optional): Usuario que da los puntitos. Si se especifica,
                                se valida la regla de admins.

    Returns:
        tuple[bool, str]: (exito, mensaje_error)
                         - exito: True si se aplicaron los puntitos, False si se bloqueó
                         - mensaje_error: Mensaje de error si se bloqueó, "" si fue exitoso

    Example:
        >>> funcion_puntitos("usuario1", 5)   # Suma 5 puntitos
        >>> funcion_puntitos("usuario2", -2)  # Resta 2 puntitos
        >>> funcion_puntitos("admin1", 5, "admin2")  # Permitido: admin2 SÍ puede dar a admin1
        >>> funcion_puntitos("admin1", 5, "hablemosdepavadaspod")  # Bloqueado: hablemosdepavadaspod no puede

    Note:
        - Los puntitos históricos se modifican igual que los actuales (pueden decrementarse,
          por ejemplo al perder un torneo de escupitajos)
        - Si el usuario no existe, se crea con los puntitos especificados
        - La validación de admins solo aplica cuando se especifica donante
    """
    # Validar regla de admins si hay donante especificado
    puede_dar, mensaje_error = validar_puntitos_admin(nombre, donante)
    if not puede_dar:
        return (False, mensaje_error)

    nombre = nombre.lower().lstrip("@")
    try:
        d1_client.upsert_puntitos(nombre, cant, cant)
    except Exception as e:
        logger.error(f"Error al actualizar puntitos de {nombre}: {e}")
        return (False, "Hubo un problema al actualizar los puntitos, probá de nuevo")

    if _bot_state is not None:
        _bot_state.puntitos_netos_sesion += cant
    return (True, "")

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
    d1_client.reset_puntitos(nombre.lower())

def _realizar_sorteo_ponderado(nombres, puntos):
    """
    Realiza un sorteo ponderado entre una lista de usuarios (función interna)

    Args:
        nombres (list): Lista de nombres de usuarios
        puntos (list): Lista de puntitos correspondientes a cada usuario

    Returns:
        str: Nombre del usuario ganador

    Note:
        - Si un usuario tiene 0 puntitos, se le asigna peso 1
        - Usuarios con más puntitos tienen mayor probabilidad de ganar
        - Esta es una función auxiliar compartida por sorteo_puntitos y sorteo_puntitos_presentes
    """
    # Ajustar pesos: si tiene 0 puntitos, ponderar por 1
    pesos = [max(1, p) for p in puntos]
    ganador = choices(nombres, weights=pesos, k=1)[0]
    return ganador

def sorteo_puntitos():
    """
    Realiza un sorteo ponderado basado en los puntitos de todos los usuarios

    Utiliza un algoritmo de selección ponderada donde usuarios con más
    puntitos tienen mayor probabilidad de ganar. El ganador tiene sus
    puntitos actuales reseteados a 0.

    IMPORTANTE:
        - Solo participan usuarios con puntitos > 0 (excluye usuarios sin puntitos)
        - Los administradores NO participan
        - Para sorteos que incluyan usuarios con 0 puntitos, usar sorteo_puntitos_presentes()

    Returns:
        str: Nombre del usuario ganador, o mensaje de error si algo falla

    Algorithm:
        - Obtiene todos los usuarios y sus puntitos
        - Filtra solo usuarios con puntitos > 0 y que no sean admins
        - Usa random.choices() con pesos basados en puntitos
        - Resetea los puntitos del ganador a 0

    Example:
        >>> sorteo_puntitos()
        'usuario_ganador'

    Error Handling:
        - Maneja errores de conexión con el Worker de D1
        - Retorna mensajes descriptivos de error
        - Registra warnings y errores en el log
    """
    try:
        df = d1_client.get_puntitos_all()
    except Exception as e:
        logger.error(f"Error en sorteo_puntitos: {e}")
        return "Error en sorteo"

    if not df:
        logger.warning("No hay datos para el sorteo")
        return "No hay participantes"

    # Filtrar usuarios: deben tener puntitos > 0 y NO ser admins
    nombres = []
    puntos = []
    for row in df:
        if row.get('puntos', 0) > 0 and row.get('nombre', '').lower() not in admins:
            nombres.append(row['nombre'])
            puntos.append(row['puntos'])

    if not nombres or not puntos:
        logger.warning("No se encontraron usuarios elegibles (con puntitos > 0 y no admins) para el sorteo")
        return "No hay participantes elegibles"

    ganador = _realizar_sorteo_ponderado(nombres, puntos)
    _reiniciar_puntitos(ganador)
    logger.info(f"Sorteo general: {ganador} ganó entre {len(nombres)} participantes")
    return ganador

def sorteo_puntitos_presentes(usuarios_activos, admins_list):
    """
    Realiza un sorteo ponderado solo entre usuarios activos (presentes en el chat)

    Similar a sorteo_puntitos(), pero solo incluye usuarios que han usado comandos
    durante la sesión actual. Excluye a los administradores del sorteo.

    Args:
        usuarios_activos (set): Conjunto de nombres de usuarios activos
        admins_list (list): Lista de nombres de administradores a excluir

    Returns:
        str: Nombre del usuario ganador, o mensaje de error si algo falla

    Algorithm:
        - Obtiene todos los usuarios y sus puntitos desde D1
        - Filtra solo usuarios activos (excluyendo admins)
        - Usa sorteo ponderado con pesos basados en puntitos (mínimo 1)
        - Resetea los puntitos del ganador a 0

    Example:
        >>> sorteo_puntitos_presentes({'user1', 'user2', 'admin'}, ['admin'])
        'user1' o 'user2'

    Error Handling:
        - Maneja errores de conexión con el Worker de D1
        - Retorna mensajes descriptivos de error si no hay participantes válidos
    """
    try:
        df = d1_client.get_puntitos_all()
    except Exception as e:
        logger.error(f"Error en sorteo_puntitos_presentes: {e}")
        return "Error en sorteo"

    if not df:
        logger.warning("No hay datos para el sorteo de presentes")
        return "No hay participantes"

    usuarios_activos_lower = {usuario.lower() for usuario in usuarios_activos}

    nombres_filtrados = []
    puntos_filtrados = []
    for row in df:
        nombre = row.get('nombre', '').lower()
        if nombre in usuarios_activos_lower and nombre not in admins_list:
            nombres_filtrados.append(row['nombre'])
            puntos_filtrados.append(row['puntos'])

    if not nombres_filtrados:
        logger.warning("No hay usuarios activos elegibles para el sorteo")
        return "No hay participantes elegibles"

    ganador = _realizar_sorteo_ponderado(nombres_filtrados, puntos_filtrados)
    _reiniciar_puntitos(ganador)
    logger.info(f"Sorteo de presentes: {ganador} ganó entre {len(nombres_filtrados)} participantes")
    return ganador

def daddy_point():
    """
    Incrementa el contador de votos para una funcionalidad especial

    Sistema de votación para eventos especiales del stream.

    Returns:
        int: Número total de votos después del incremento

    Note:
        - Funcionalidad especial/easter egg del bot
    """
    return d1_client.incrementar_daddy_points()

def get_programacion():
    """
    Obtiene la programación semanal desde D1

    Returns:
        list: Lista de strings con la programación semanal,
              o lista con mensaje de error si falla la conexión

    Example:
        >>> get_programacion()
        ['Lunes 20:00 - Juego A', 'Miércoles 19:00 - Juego B']
    """
    try:
        programacion_lista = d1_client.get_programacion()
    except Exception as e:
        logger.error(f"Error en get_programacion: {e}")
        return ["Error: No se pudo acceder a la programación"]

    if not programacion_lista:
        logger.warning("La programación está vacía")
        return ["Error: No se pudo cargar la programación - vacía"]

    logger.info(f"Programación cargada exitosamente: {len(programacion_lista)} elementos")
    return programacion_lista

def get_restricciones_escupir():
    """
    Obtiene las restricciones configurables para el comando !escupir desde D1

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

    Error Handling:
        - Maneja errores de conexión con el Worker de D1
        - Retorna lista vacía si falla la lectura
    """
    try:
        restricciones_raw = d1_client.get_restricciones_escupir()
    except Exception as e:
        logger.error(f"Error en get_restricciones_escupir: {e}")
        return []

    restricciones = []
    for row in restricciones_raw:
        penalizacion = int(row.get('penalizacion', 0) or 0)
        # IMPORTANTE: Las restricciones NUNCA suman puntos, solo restan o son neutras
        if penalizacion > 0:
            logger.warning(f"Restricción con penalización positiva detectada ({penalizacion}), se convertirá a negativa: -{penalizacion}")
            penalizacion = -penalizacion

        restricciones.append({
            'dia': str(row.get('dia', '')).strip(),
            'hora_inicio': str(row.get('hora_inicio', '')).strip(),
            'hora_fin': str(row.get('hora_fin', '')).strip(),
            'penalizacion': penalizacion,
            'mensaje': str(row.get('mensaje', '')).strip(),
        })

    logger.info(f"Restricciones de escupir cargadas: {len(restricciones)} reglas")
    return restricciones

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

def _registrar_en_victorias(nombre: str, campo: str, cant: int = 1) -> bool:
    """Helper interno: suma `cant` en el campo `campo` de la tabla victorias para el usuario."""
    try:
        d1_client.incrementar_victoria(nombre, campo, cant)
        logger.info(f"{campo} actualizado para {nombre}")
        return True
    except Exception as e:
        logger.error(f"Error registrando {campo} para {nombre}: {e}")
        return False

def registrar_victoria_sorteo(nombre: str):
    _registrar_en_victorias(nombre.lower().lstrip("@"), campo='sorteos_ganados')

def registrar_victoria_torneo(nombre: str, cant: int = 1):
    _registrar_en_victorias(nombre.lower().lstrip("@"), campo='torneos_ganados', cant=cant)

def consulta_victorias(nombre: str):
    """
    Consulta las victorias (sorteos, torneos, timbas, margaritas) y récord de escupitajo de un usuario

    Retorna un diccionario con la cantidad de sorteos, torneos, timbas, margaritas ganadas
    y el récord de escupitajo del usuario.

    Args:
        nombre (str): Nombre del usuario (se normaliza automáticamente)

    Returns:
        dict: Diccionario con 'sorteos_ganados', 'torneos_ganados', 'timbas_ganadas', 'margaritas_ganadas',
              'escupitajo_record' y 'jackpots_ganados'
              Retorna todos los valores en 0 si no existe

    Example:
        >>> consulta_victorias("usuario1")
        {'sorteos_ganados': 3, 'torneos_ganados': 5, 'timbas_ganadas': 2, 'margaritas_ganadas': 4, 'escupitajo_record': 450, 'jackpots_ganados': 1}
        >>> consulta_victorias("usuario_nuevo")
        {'sorteos_ganados': 0, 'torneos_ganados': 0, 'timbas_ganadas': 0, 'margaritas_ganadas': 0, 'escupitajo_record': 0, 'jackpots_ganados': 0}
    """
    nombre = nombre.lower().lstrip("@")
    ceros = {
        'sorteos_ganados': 0,
        'torneos_ganados': 0,
        'timbas_ganadas': 0,
        'margaritas_ganadas': 0,
        'escupitajo_record': 0,
        'jackpots_ganados': 0,
    }

    try:
        df = d1_client.get_victorias_all()
    except Exception as e:
        logger.error(f"Error al consultar victorias para {nombre}: {e}")
        return ceros

    for row in df:
        if row.get('nombre') == nombre:
            return {
                'sorteos_ganados': int(row.get('sorteos_ganados', 0) or 0),
                'torneos_ganados': int(row.get('torneos_ganados', 0) or 0),
                'timbas_ganadas': int(row.get('timbas_ganadas', 0) or 0),
                'margaritas_ganadas': int(row.get('margaritas_ganadas', 0) or 0),
                'escupitajo_record': int(row.get('escupitajo_record', 0) or 0),
                'jackpots_ganados': int(row.get('jackpots_ganados', 0) or 0),
            }

    return ceros

def registrar_victoria_timba(nombre: str):
    _registrar_en_victorias(nombre.lower().lstrip("@"), campo='timbas_ganadas')

def registrar_victoria_margarita(nombre: str):
    _registrar_en_victorias(nombre.lower().lstrip("@"), campo='margaritas_ganadas')

def registrar_victoria_jackpot(nombre: str):
    _registrar_en_victorias(nombre.lower().lstrip("@"), campo='jackpots_ganados')

def registrar_record_escupitajo(nombre: str, distancia: int) -> bool:
    """Actualiza el récord de escupitajo solo si la nueva distancia es mayor. Retorna True si hubo nuevo récord."""
    nombre = nombre.lower().lstrip("@")
    try:
        nuevo_record, record = d1_client.registrar_record_escupitajo_remoto(nombre, distancia)
    except Exception as e:
        logger.error(f"Error registrando récord de escupitajo para {nombre}: {e}")
        return False

    if nuevo_record:
        logger.info(f"Nuevo récord de escupitajo para {nombre}: {record} cm")
    return nuevo_record

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

    Note:
        - Solo incluye usuarios con récords > 0
        - Ordena de mayor a menor distancia
        - Si hay menos de N usuarios con récords, retorna todos los disponibles
    """
    try:
        df = d1_client.get_victorias_all()
    except Exception as e:
        logger.error(f"Error al obtener top récords de escupitajo: {e}")
        return []

    records = [
        (row['nombre'], int(row.get('escupitajo_record', 0) or 0))
        for row in df
        if row.get('nombre') and int(row.get('escupitajo_record', 0) or 0) > 0
    ]
    records.sort(key=lambda x: x[1], reverse=True)
    return records[:n]


# ─── Memoria de Claudio ────────────────────────────────────────────────────────

def get_memoria_claude(username: str) -> str:
    """
    Lee el resumen de memoria de un usuario

    Args:
        username (str): Nombre del usuario (en minúsculas)

    Returns:
        str: Resumen guardado, o "" si el usuario no tiene memoria aún
    """
    try:
        return d1_client.get_claude_memoria(username)
    except Exception as e:
        logger.error(f"Claude memoria - Error al leer memoria de {username}: {e}")
        return ""

def guardar_memoria_claude(username: str, resumen: str) -> None:
    """
    Guarda o actualiza el resumen de memoria de un usuario.
    Si el usuario ya tiene registro lo actualiza; si no, lo crea.

    Args:
        username (str): Nombre del usuario (en minúsculas)
        resumen (str): Resumen generado por Claude
    """
    try:
        d1_client.set_claude_memoria(username, resumen)
        logger.info(f"Claude memoria - Memoria guardada para {username}")
    except Exception as e:
        logger.error(f"Claude memoria - Error al guardar memoria de {username}: {e}")
