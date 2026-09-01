// Autenticación simple por Bearer token. A diferencia del worker de puntitos,
// ACÁ TODAS las rutas requieren auth — este worker solo sirve credenciales.

export function isAuthorized(request: Request, readKey: string): boolean {
  const header = request.headers.get("Authorization") ?? "";
  const [scheme, token] = header.split(" ");
  return scheme === "Bearer" && token === readKey;
}
