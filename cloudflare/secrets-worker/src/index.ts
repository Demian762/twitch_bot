import { isAuthorized } from "./auth";

export interface Env {
  DB: D1Database;
  READ_KEY: string;
}

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (request.method !== "GET" || url.pathname !== "/secrets") {
      return json({ error: "not found" }, 404);
    }

    if (!isAuthorized(request, env.READ_KEY)) {
      return json({ error: "unauthorized" }, 401);
    }

    const { results } = await env.DB.prepare("SELECT key, value FROM secrets").all<{
      key: string;
      value: string;
    }>();

    const out: Record<string, string> = {};
    for (const row of results ?? []) out[row.key] = row.value;

    return json(out);
  },
};
