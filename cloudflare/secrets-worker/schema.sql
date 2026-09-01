-- Schema D1 para el store de secretos remotos de BotDelEstadio.
-- Un blob clave/valor: cada fila es una variable de utils/secretos.py.
-- Aplicar con: wrangler d1 execute botdelestadio_secrets --remote --file=schema.sql

CREATE TABLE IF NOT EXISTS secrets (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
