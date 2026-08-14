"""
Script de migración única: vuelca el Google Sheet de puntitos a un seed.sql
para D1.

Es de SOLO LECTURA contra el Sheet — no modifica nada ahí. Genera
cloudflare/worker/seed.sql con INSERTs para revisar a mano antes de correrlo
contra la base real:

    npx wrangler d1 execute botdelestadio_db --remote --file=seed.sql

Uso: python cloudflare/migrate_from_sheets.py
(correr desde la raíz del repo, con el venv del bot activado — reutiliza las
credenciales de utils/secretos.py)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gspread
from utils.secretos import credenciales_gspread, file_puntitos_url


def sql_str(value) -> str:
    """Escapa un string para uso literal en SQL (comillas simples)."""
    return "'" + str(value).replace("'", "''") + "'"


def main() -> None:
    gc = gspread.service_account_from_dict(credenciales_gspread)
    sh = gc.open_by_url(file_puntitos_url)

    lineas = ["-- Generado por cloudflare/migrate_from_sheets.py — revisar antes de aplicar.", ""]

    # ─── puntitos (hoja 1) ──────────────────────────────────────────────
    puntitos = sh.sheet1.get_all_records()
    lineas.append("-- puntitos")
    for row in puntitos:
        nombre = str(row["nombre"]).lower().lstrip("@")
        lineas.append(
            f"INSERT INTO puntitos (nombre, puntos, historico) VALUES "
            f"({sql_str(nombre)}, {int(row['puntos'])}, {int(row['historico'])});"
        )
    lineas.append("")

    # ─── daddy_points (hoja 2) ──────────────────────────────────────────
    daddy = sh.get_worksheet(1).get_all_records()
    votos = int(daddy[0]["daddy_points"]) if daddy else 0
    lineas.append("-- daddy_points")
    lineas.append(f"UPDATE daddy_points SET votos = {votos} WHERE id = 1;")
    lineas.append("")

    # ─── programacion (hoja 3) ──────────────────────────────────────────
    programacion = sh.get_worksheet(2).get_all_records()
    lineas.append("-- programacion")
    for i, row in enumerate(programacion):
        if "programacion" in row:
            lineas.append(
                f"INSERT INTO programacion (orden, texto) VALUES ({i}, {sql_str(row['programacion'])});"
            )
    lineas.append("")

    # ─── restricciones_escupir (hoja 4) ──────────────────────────────────
    restricciones = sh.get_worksheet(3).get_all_records()
    lineas.append("-- restricciones_escupir")
    for row in restricciones:
        if not all(k in row for k in ("dia", "penalizacion", "mensaje")):
            continue
        lineas.append(
            "INSERT INTO restricciones_escupir (dia, hora_inicio, hora_fin, penalizacion, mensaje) VALUES "
            f"({sql_str(row['dia'])}, {sql_str(row.get('hora_inicio', ''))}, "
            f"{sql_str(row.get('hora_fin', ''))}, {int(row['penalizacion'] or 0)}, {sql_str(row['mensaje'])});"
        )
    lineas.append("")

    # ─── victorias (hoja 5) ───────────────────────────────────────────────
    victorias = sh.get_worksheet(4).get_all_records()
    lineas.append("-- victorias")
    for row in victorias:
        nombre = str(row.get("nombre", "")).lower().lstrip("@")
        if not nombre:
            continue
        lineas.append(
            "INSERT INTO victorias (nombre, sorteos_ganados, torneos_ganados, timbas_ganadas, "
            "margaritas_ganadas, escupitajo_record) VALUES "
            f"({sql_str(nombre)}, {int(row.get('sorteos_ganados', 0) or 0)}, "
            f"{int(row.get('torneos_ganados', 0) or 0)}, {int(row.get('timbas_ganadas', 0) or 0)}, "
            f"{int(row.get('margaritas_ganadas', 0) or 0)}, {int(row.get('escupitajo_record', 0) or 0)});"
        )
    lineas.append("")

    # ─── claude_memoria (hoja "Claude") ───────────────────────────────────
    try:
        claude_rows = sh.worksheet("Claude").get_all_records()
    except gspread.exceptions.WorksheetNotFound:
        claude_rows = []
    lineas.append("-- claude_memoria")
    for row in claude_rows:
        usuario = str(row.get("usuario", "")).lower()
        if not usuario:
            continue
        lineas.append(
            "INSERT INTO claude_memoria (usuario, resumen, ultima_actualizacion) VALUES "
            f"({sql_str(usuario)}, {sql_str(row.get('resumen', ''))}, "
            f"{sql_str(row.get('ultima_actualizacion', ''))});"
        )

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "worker", "seed.sql")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")

    print(f"OK: {len(puntitos)} puntitos, {len(programacion)} filas de programación, "
          f"{len(restricciones)} restricciones, {len(victorias)} victorias, "
          f"{len(claude_rows)} memorias de Claude.")
    print(f"Generado: {out_path}")
    print("Revisalo antes de aplicarlo con: npx wrangler d1 execute botdelestadio_db --remote --file=seed.sql")


if __name__ == "__main__":
    main()
