"""Home Assistant vu depuis l'add-on : l'API REST du core, via le proxy du Supervisor."""

from neo_box.features.app.infra.http import HttpError, request_json

PERMIT_JOIN_SECONDS = 120


class HomeAssistantClient:
    """Appels REST authentifies par le jeton du Supervisor."""

    def __init__(self, base_url: str, token: str) -> None:
        """`base_url` est l'URL de l'API (ex. http://supervisor/core/api)."""
        self._base = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {token}"}

    def ping(self) -> bool:
        """True si l'API repond (GET /)."""
        try:
            request_json("GET", f"{self._base}/", headers=self._headers, timeout=5.0)
        except HttpError:
            return False
        return True

    def permit_join(self, seconds: int = PERMIT_JOIN_SECONDS) -> None:
        """Ouvre le reseau ZHA a l'appairage (service `zha.permit`)."""
        request_json(
            "POST",
            f"{self._base}/services/zha/permit",
            headers=self._headers,
            body={"duration": seconds},
            timeout=10.0,
        )
