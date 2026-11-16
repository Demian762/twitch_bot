-- Schema D1 para el sistema de puntitos de BotDelEstadio.
-- Espeja 1:1 las 6 hojas del Google Sheet que reemplaza.
-- Aplicar con: wrangler d1 execute botdelestadio_db --remote --file=schema.sql

CREATE TABLE IF NOT EXISTS puntitos (
  nombre    TEXT PRIMARY KEY,
  puntos    INTEGER NOT NULL DEFAULT 0,
  historico INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS victorias (
  nombre              TEXT PRIMARY KEY,
  sorteos_ganados     INTEGER NOT NULL DEFAULT 0,
  torneos_ganados     INTEGER NOT NULL DEFAULT 0,
  timbas_ganadas      INTEGER NOT NULL DEFAULT 0,
  margaritas_ganadas  INTEGER NOT NULL DEFAULT 0,
  escupitajo_record   INTEGER NOT NULL DEFAULT 0,
  jackpots_ganados    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS programacion (
  orden INTEGER PRIMARY KEY,
  texto TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS restricciones_escupir (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  dia           TEXT NOT NULL,
  hora_inicio   TEXT NOT NULL DEFAULT '',
  hora_fin      TEXT NOT NULL DEFAULT '',
  penalizacion  INTEGER NOT NULL DEFAULT 0,
  mensaje       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS daddy_points (
  id     INTEGER PRIMARY KEY CHECK (id = 1),
  votos  INTEGER NOT NULL DEFAULT 0
);
INSERT OR IGNORE INTO daddy_points (id, votos) VALUES (1, 0);

CREATE TABLE IF NOT EXISTS claude_memoria (
  usuario              TEXT PRIMARY KEY,
  resumen              TEXT NOT NULL,
  ultima_actualizacion TEXT NOT NULL
);

-- Avisos de !avisar. Cada fila se borra en cuanto el aviso le llega a alguno de sus
-- destinatarios. Fechas en hora argentina (UTC-3 fijo), formato 'YYYY-MM-DD HH:MM:SS'.
CREATE TABLE IF NOT EXISTS recordatorios (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  creador       TEXT NOT NULL,   -- quién usó !avisar
  destinatarios TEXT NOT NULL,   -- usuarios separados por coma, en minúscula y sin @
  titulo        TEXT NOT NULL,   -- resumen corto, para !avisos
  mensaje       TEXT NOT NULL,   -- texto del aviso ya redactado, sin las menciones
  vence         TEXT NOT NULL,
  creado        TEXT NOT NULL,
  pedido        TEXT NOT NULL    -- texto original del comando
);
