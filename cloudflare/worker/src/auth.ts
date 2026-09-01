// Autenticación simple por Bearer token para las rutas de escritura (POST).
// Las rutas de lectura (GET) son públicas — ver src/index.ts.

export function isAuthorized(request: Request, apiToken: string): boolean {
  const header = request.headers.get("Authorization") ?? "";
  const [scheme, token] = header.split(" ");
  return scheme === "Bearer" && token === apiToken;
}
