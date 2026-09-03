"""Le Supervisor de Home Assistant OS : hote, reseau, core."""

from typing import Any

from neo_box.features.app.infra.http import HttpError, request_json


class SupervisorClient:
    """Appels a l'API du Supervisor (http://supervisor depuis un add-on)."""

    def __init__(self, base_url: str, token: str) -> None:
        """`token` est le SUPERVISOR_TOKEN injecte dans l'add-on."""
        self._base = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {token}"}

    def host_info(self) -> dict[str, Any]:
        """Hostname, disque, etc. (`data` de GET /host/info) ; vide si injoignable."""
        return self._data("GET", "/host/info")

    def core_info(self) -> dict[str, Any]:
        """Version et etat du core (`data` de GET /core/info) ; vide si injoignable."""
        return self._data("GET", "/core/info")

    def network_info(self) -> dict[str, Any]:
        """Interfaces et adresses (`data` de GET /network/info) ; vide si injoignable."""
        return self._data("GET", "/network/info")

    def reboot_host(self) -> None:
        """Redemarre le Raspberry."""
        request_json("POST", f"{self._base}/host/reboot", headers=self._headers, timeout=10.0)

    def _data(self, method: str, path: str) -> dict[str, Any]:
        try:
            payload = request_json(method, f"{self._base}{path}", headers=self._headers)
        except HttpError:
            return {}
        data = payload.get("data") if isinstance(payload, dict) else None
        return data if isinstance(data, dict) else {}
