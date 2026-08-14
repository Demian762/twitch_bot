// Helpers de queries D1. Cada función corresponde a una operación que antes
// hacía utils/puntitos_manager.py directamente contra el Google Sheet.

export interface PuntitosRow {
  nombre: string;
  puntos: number;
  historico: number;
}

export interface VictoriasRow {
  nombre: string;
  sorteos_ganados: number;
  torneos_ganados: number;
  timbas_ganadas: number;
  margaritas_ganadas: number;
  escupitajo_record: number;
}

export interface RestriccionRow {
  dia: string;
  hora_inicio: string;
  hora_fin: string;
  penalizacion: number;
  mensaje: string;
}

const CAMPOS_VICTORIA = new Set([
  "sorteos_ganados",
  "torneos_ganados",
  "timbas_ganadas",
  "margaritas_ganadas",
]);

export async function getPuntitosAll(db: D1Database): Promise<PuntitosRow[]> {
  const { results } = await db.prepare("SELECT nombre, puntos, historico FROM puntitos").all<PuntitosRow>();
  return results ?? [];
}

export async function upsertPuntitos(
  db: D1Database,
  nombre: string,
  deltaPuntos: number,
  deltaHistorico: number
): Promise<{ puntos: number; historico: number }> {
  const row = await db
    .prepare(
      `INSERT INTO puntitos (nombre, puntos, historico) VALUES (?1, ?2, ?3)
       ON CONFLICT(nombre) DO UPDATE SET
         puntos = puntos + excluded.puntos,
         historico = historico + excluded.historico
       RETURNING puntos, historico`
    )
    .bind(nombre, deltaPuntos, deltaHistorico)
    .first<{ puntos: number; historico: number }>();
  if (!row) throw new Error("upsertPuntitos no devolvió fila");
  return row;
}

export async function resetPuntitos(db: D1Database, nombre: string): Promise<void> {
  await db.prepare("UPDATE puntitos SET puntos = 0 WHERE nombre = ?1").bind(nombre).run();
}

export async function getVictoriasAll(db: D1Database): Promise<VictoriasRow[]> {
  const { results } = await db.prepare("SELECT * FROM victorias").all<VictoriasRow>();
  return results ?? [];
}

export async function incrementarVictoria(
  db: D1Database,
  nombre: string,
  campo: string,
  cant: number
): Promise<number> {
  if (!CAMPOS_VICTORIA.has(campo)) {
    throw new Error(`Campo de victoria inválido: ${campo}`);
  }
  // `campo` está whitelisteado arriba, es seguro interpolarlo en el SQL.
  const row = await db
    .prepare(
      `INSERT INTO victorias (nombre, ${campo}) VALUES (?1, ?2)
       ON CONFLICT(nombre) DO UPDATE SET ${campo} = ${campo} + excluded.${campo}
       RETURNING ${campo} AS valor`
    )
    .bind(nombre, cant)
    .first<{ valor: number }>();
  return row?.valor ?? cant;
}

export async function registrarRecordEscupitajo(
  db: D1Database,
  nombre: string,
  distancia: number
): Promise<{ nuevoRecord: boolean; record: number }> {
  const update = await db
    .prepare("UPDATE victorias SET escupitajo_record = ?1 WHERE nombre = ?2 AND escupitajo_record < ?1")
    .bind(distancia, nombre)
    .run();

  if ((update.meta.changes ?? 0) > 0) {
    return { nuevoRecord: true, record: distancia };
  }

  const existente = await db
    .prepare("SELECT escupitajo_record FROM victorias WHERE nombre = ?1")
    .bind(nombre)
    .first<{ escupitajo_record: number }>();

  if (!existente) {
    await db
      .prepare("INSERT INTO victorias (nombre, escupitajo_record) VALUES (?1, ?2)")
      .bind(nombre, distancia)
      .run();
    return { nuevoRecord: true, record: distancia };
  }

  return { nuevoRecord: false, record: existente.escupitajo_record };
}

export async function getProgramacion(db: D1Database): Promise<string[]> {
  const { results } = await db.prepare("SELECT texto FROM programacion ORDER BY orden").all<{ texto: string }>();
  return (results ?? []).map((r) => r.texto);
}

export async function getRestriccionesEscupir(db: D1Database): Promise<RestriccionRow[]> {
  const { results } = await db
    .prepare("SELECT dia, hora_inicio, hora_fin, penalizacion, mensaje FROM restricciones_escupir")
    .all<RestriccionRow>();
  return results ?? [];
}

export async function getDaddyPoints(db: D1Database): Promise<number> {
  const row = await db.prepare("SELECT votos FROM daddy_points WHERE id = 1").first<{ votos: number }>();
  return row?.votos ?? 0;
}

export async function incrementarDaddyPoints(db: D1Database): Promise<number> {
  const row = await db
    .prepare("UPDATE daddy_points SET votos = votos + 1 WHERE id = 1 RETURNING votos")
    .first<{ votos: number }>();
  return row?.votos ?? 0;
}

export async function getClaudeMemoria(db: D1Database, usuario: string): Promise<string> {
  const row = await db
    .prepare("SELECT resumen FROM claude_memoria WHERE usuario = ?1")
    .bind(usuario)
    .first<{ resumen: string }>();
  return row?.resumen ?? "";
}

export async function setClaudeMemoria(db: D1Database, usuario: string, resumen: string): Promise<void> {
  const fecha = new Date().toISOString().slice(0, 16).replace("T", " ");
  await db
    .prepare(
      `INSERT INTO claude_memoria (usuario, resumen, ultima_actualizacion) VALUES (?1, ?2, ?3)
       ON CONFLICT(usuario) DO UPDATE SET resumen = excluded.resumen, ultima_actualizacion = excluded.ultima_actualizacion`
    )
    .bind(usuario, resumen, fecha)
    .run();
}
