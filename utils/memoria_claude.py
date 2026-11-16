"""
Control de formato y largo de la memoria por usuario de !bot (tabla claude_memoria de D1).

El modelo no cuenta caracteres bien, así que el prompt (PROMPT_MEMORIA) pide los límites
y este módulo los verifica después de generar. Si algo se pasa, claude_commands pide una
segunda pasada de compresión; si vuelve a pasarse, se conserva la memoria anterior.
"""

import re

CAMPOS = ("NOMBRE", "TRATO", "PERFIL", "INTERESES")

# Los mismos límites que pide PROMPT_MEMORIA
LIMITES_CARACTERES = {"NOMBRE": 100, "TRATO": 250, "PERFIL": 300, "INTERESES": 150}
MAX_INTERESES = 10

# Margen sobre los límites antes de pedir una compresión: pasarse por pocos
# caracteres no justifica una llamada extra
TOLERANCIA = 1.15

# Respuesta del modelo cuando la conversación no aporta nada nuevo
SIN_CAMBIOS = "SIN CAMBIOS"

_VACIOS = {"(no indicado)", "(estándar)", ""}
_LINEA = re.compile(r"^(NOMBRE|TRATO|PERFIL|INTERESES):[ \t]*(.*)$")


def parsear(resumen: str) -> dict | None:
    """Devuelve {campo: valor} si el resumen tiene exactamente los 4 campos, cada uno en su línea."""
    campos = {}
    for linea in resumen.strip().splitlines():
        if not linea.strip():
            continue
        m = _LINEA.match(linea.strip())
        if not m or m.group(1) in campos:
            return None
        campos[m.group(1)] = m.group(2).strip()
    if set(campos) != set(CAMPOS):
        return None
    return campos


def contar_intereses(valor: str) -> int:
    if valor in _VACIOS:
        return 0
    return len([t for t in valor.split(",") if t.strip()])


def problemas(resumen: str) -> list[str]:
    """Lista de problemas del resumen (vacía si está bien), redactados para pasárselos al modelo."""
    campos = parsear(resumen)
    if campos is None:
        return ["el formato no es válido: tienen que ser exactamente 4 líneas, NOMBRE, TRATO, PERFIL e INTERESES"]
    fallas = []
    for campo in CAMPOS:
        valor, limite = campos[campo], LIMITES_CARACTERES[campo]
        if not valor:
            fallas.append(f"{campo} está vacío")
        elif len(valor) > limite * TOLERANCIA:
            fallas.append(f"{campo} tiene {len(valor)} caracteres (máximo {limite})")
    n = contar_intereses(campos["INTERESES"])
    if n > MAX_INTERESES:
        fallas.append(f"INTERESES tiene {n} términos (máximo {MAX_INTERESES})")
    return fallas


def prompt_compresion(resumen: str, fallas: list[str]) -> str:
    """Mensaje de usuario para la segunda pasada, cuando el resumen se pasó de los límites."""
    return (
        "Este resumen no cumple los límites:\n"
        + "\n".join(f"- {f}" for f in fallas)
        + "\n\nReescribilo con el mismo formato, comprimiendo solo lo que se pasó: dejá lo más "
        "relevante y reciente, y nunca pierdas los pedidos explícitos del usuario en TRATO. "
        f"No respondas {SIN_CAMBIOS}.\n\n" + resumen.strip()
    )
