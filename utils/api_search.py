"""
Búsqueda web via Brave Search API

Proporciona búsqueda web general para el comando !claudio cuando necesita
información reciente que RAWG o Steam no cubren.

Documentación: https://api.search.brave.com/app/documentation/web-search/get-started
Free tier: 2000 queries/mes
"""

import requests
from utils.logger import logger


class BraveSearch:

    URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def search(self, query: str, count: int = 4) -> str:
        """Busca en la web y retorna un resumen de los primeros resultados."""
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key,
        }
        params = {
            "q": query,
            "count": min(count, 5),
            "search_lang": "es",
            "country": "AR",
        }

        response = None
        for intento in range(3):
            try:
                response = requests.get(self.URL, headers=headers, params=params, timeout=10)
                if response.status_code == 200:
                    break
                logger.warning(f"Brave Search - Intento {intento+1}/3 falló: status {response.status_code}")
            except Exception as e:
                logger.warning(f"Brave Search - Intento {intento+1}/3 error: {e}")

        if response is None or response.status_code != 200:
            logger.error(f"Brave Search - No se pudo obtener resultados para: {query!r}")
            return "Error al buscar en la web."

        results = response.json().get("web", {}).get("results", [])
        if not results:
            return "No se encontraron resultados."

        lines = []
        for r in results[:count]:
            title = r.get("title", "")
            desc = r.get("description", "")
            if len(desc) > 200:
                desc = desc[:197] + "..."
            lines.append(f"• {title}: {desc}" if desc else f"• {title}")

        logger.info(f"Brave Search - Búsqueda exitosa para: {query!r} ({len(results)} resultados)")
        return "\n".join(lines)
