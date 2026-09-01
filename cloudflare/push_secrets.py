"""
Genera cloudflare/secrets-worker/seed.sql a partir de utils/secretos.py local,
para sincronizar los secretos remotos que consume utils/secrets_bootstrap.py
en cada PC donde corre el bot.

Es de SOLO LECTURA contra secretos.py — no lo modifica. Volca cada variable
de nivel superior (excepto las que empiezan con "_") como una fila
clave/valor, usando repr() para que el valor se pueda pegar tal cual en un
`nombre = <repr>` de Python del lado del bootstrap.

Uso: python cloudflare/push_secrets.py
(correr desde la raíz del repo, con el venv del bot activado)

Revisar el seed.sql generado antes de aplicarlo:
    npx wrangler d1 execute botdelestadio_secrets --remote --file=seed.sql
(desde cloudflare/secrets-worker/)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import secretos

SERIALIZABLE_TYPES = (str, int, float, bool, dict, list, tuple)


def sql_str(value: str) -> str:
    """Escapa un string para uso literal en SQL (comillas simples)."""
    return "'" + value.replace("'", "''") + "'"


def main() -> None:
    nombres = [
        n for n in dir(secretos)
        if not n.startswith("_") and isinstance(getattr(secretos, n), SERIALIZABLE_TYPES)
    ]

    lineas = ["-- Generado por cloudflare/push_secrets.py — revisar antes de aplicar.", ""]
    for nombre in sorted(nombres):
        valor = getattr(secretos, nombre)
        lineas.append(
            "INSERT INTO secrets (key, value) VALUES "
            f"({sql_str(nombre)}, {sql_str(repr(valor))}) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value;"
        )

    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "secrets-worker", "seed.sql"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")

    print(f"OK: {len(nombres)} variables volcadas desde utils/secretos.py.")
    print(f"Generado: {out_path}")
    print(
        "Revisalo y aplicalo con (desde cloudflare/secrets-worker/):\n"
        "  npx wrangler d1 execute botdelestadio_secrets --remote --file=seed.sql"
    )


if __name__ == "__main__":
    main()
