import { isAuthorized } from "./auth";
import {
  getPuntitosAll,
  upsertPuntitos,
  resetPuntitos,
  getVictoriasAll,
  incrementarVictoria,
  registrarRecordEscupitajo,
  getProgramacion,
  getRestriccionesEscupir,
  getDaddyPoints,
  incrementarDaddyPoints,
  getClaudeMemoria,
  setClaudeMemoria,
} from "./db";

export interface Env {
  DB: D1Database;
  API_TOKEN: string;
}

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...CORS_HEADERS },
  });
}

function unauthorized(): Response {
  return json({ error: "unauthorized" }, 401);
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const { pathname } = url;
    const method = request.method;

    if (method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    try {
      // ─── Lectura pública ────────────────────────────────────────────
      if (method === "GET" && pathname === "/puntitos") {
        return json(await getPuntitosAll(env.DB));
      }
      if (method === "GET" && pathname === "/victorias") {
        return json(await getVictoriasAll(env.DB));
      }
      if (method === "GET" && pathname === "/programacion") {
        return json(await getProgramacion(env.DB));
      }
      if (method === "GET" && pathname === "/restricciones_escupir") {
        return json(await getRestriccionesEscupir(env.DB));
      }
      if (method === "GET" && pathname === "/daddy_points") {
        return json({ votos: await getDaddyPoints(env.DB) });
      }
      const memoriaMatch = pathname.match(/^\/claude_memoria\/([^/]+)$/);
      if (method === "GET" && memoriaMatch) {
        const usuario = decodeURIComponent(memoriaMatch[1]);
        return json({ resumen: await getClaudeMemoria(env.DB, usuario) });
      }

      // ─── Escritura, requiere Bearer token ──────────────────────────
      if (method === "POST") {
        if (!isAuthorized(request, env.API_TOKEN)) return unauthorized();
        const body = await request.json<Record<string, unknown>>().catch(() => ({}));

        if (pathname === "/puntitos/upsert") {
          const { nombre, delta_puntos, delta_historico } = body as {
            nombre: string;
            delta_puntos: number;
            delta_historico: number;
          };
          return json(await upsertPuntitos(env.DB, nombre, delta_puntos, delta_historico));
        }

        if (pathname === "/puntitos/reset") {
          const { nombre } = body as { nombre: string };
          await resetPuntitos(env.DB, nombre);
          return json({ ok: true });
        }

        if (pathname === "/victorias/incrementar") {
          const { nombre, campo, cant } = body as { nombre: string; campo: string; cant: number };
          const valor = await incrementarVictoria(env.DB, nombre, campo, cant);
          return json({ valor });
        }

        if (pathname === "/victorias/record_escupitajo") {
          const { nombre, distancia } = body as { nombre: string; distancia: number };
          const resultado = await registrarRecordEscupitajo(env.DB, nombre, distancia);
          return json(resultado);
        }

        if (pathname === "/daddy_points/incrementar") {
          return json({ votos: await incrementarDaddyPoints(env.DB) });
        }

        if (pathname === "/claude_memoria") {
          const { usuario, resumen } = body as { usuario: string; resumen: string };
          await setClaudeMemoria(env.DB, usuario, resumen);
          return json({ ok: true });
        }
      }

      return json({ error: "not found" }, 404);
    } catch (err) {
      return json({ error: String(err) }, 500);
    }
  },
};
