"""Un client HTTP minimal sur urllib : pas de dependance, des delais courts, des erreurs typees."""

import json
from typing import Any
from urllib import error, request


class HttpError(Exception):
    """La requete a echoue (reseau, delai, ou statut non 2xx)."""

    def __init__(self, url: str, status: int | None, reason: str) -> None:
        """Garde de quoi comprendre l'echec dans un log."""
        super().__init__(f"{url} -> {status}: {reason}")
        self.url = url
        self.status = status


def request_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    timeout: float = 5.0,
) -> Any:  # noqa: ANN401 - le JSON decode est libre par nature
    """Envoie une requete JSON et decode la reponse (None si le corps est vide)."""
    data = json.dumps(body).encode() if body is not None else None
    sent_headers = {"Content-Type": "application/json", **(headers or {})}
    req = request.Request(url, data=data, headers=sent_headers, method=method)  # noqa: S310
    try:
        with request.urlopen(req, timeout=timeout) as response:  # noqa: S310 - URL de config
            raw = response.read()
    except error.HTTPError as exc:
        raise HttpError(url, exc.code, exc.reason) from exc
    except (error.URLError, TimeoutError, OSError) as exc:
        raise HttpError(url, None, str(exc)) from exc
    return json.loads(raw) if raw else None
