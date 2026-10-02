"""Le backend Neo vu depuis la box : annonce, heartbeat, demande d'assistance.

Contrat : backend/src/modules/boxes (routes /api/boxes/announce et /api/boxes/me/*).
"""

import logging
from collections.abc import Callable
from typing import Any

from neo_box.features.app.infra.http import HttpError, request_json
from neo_box.features.status.domain.state import BoxState

_LOGGER = logging.getLogger(__name__)

CredentialsProvider = Callable[[], str | None]


class BackendClient:
    """Appels HTTP au backend ; la cle API est relue a chaque appel (elle arrive en route)."""

    def __init__(self, base_url: str, api_key: CredentialsProvider) -> None:
        """`api_key` rend la cle courante ou None tant que la box n'est pas enrolee."""
        self._base = base_url.rstrip("/")
        self._api_key = api_key

    def announce(self, token: str, hardware_id: str, version: str) -> dict[str, Any]:
        """Se presente avec le jeton ; la reponse porte la cle une fois la box rattachee."""
        payload = request_json(
            "POST",
            f"{self._base}/api/boxes/announce",
            body={"provisioning_token": token, "hardware_id": hardware_id, "version": version},
            timeout=10.0,
        )
        return payload if isinstance(payload, dict) else {}

    def heartbeat(self, state: BoxState, error_code: str | None) -> None:
        """Telemetrie periodique (box enrolee uniquement)."""
        request_json(
            "POST",
            f"{self._base}/api/boxes/me/heartbeat",
            headers=self._auth(),
            body={"version": state.version, "error_code": error_code, "state": _telemetry(state)},
            timeout=10.0,
        )

    def request_support(self) -> dict[str, Any]:
        """Ouvre (ou retrouve) une demande d'assistance a distance."""
        payload = request_json(
            "POST",
            f"{self._base}/api/boxes/me/support-requests",
            headers=self._auth(),
            body={},
            timeout=10.0,
        )
        return payload if isinstance(payload, dict) else {}

    def pairing_code(self) -> dict[str, Any]:
        """Demande un code d'appairage client frais (usage unique, courte duree)."""
        payload = request_json(
            "POST",
            f"{self._base}/api/boxes/me/pairing-code",
            headers=self._auth(),
            body={},
            timeout=10.0,
        )
        return payload if isinstance(payload, dict) else {}

    def get_config(self) -> dict[str, Any]:
        """Tire la configuration désirée (GET /api/boxes/me/config)."""
        payload = request_json(
            "GET",
            f"{self._base}/api/boxes/me/config",
            headers=self._auth(),
            timeout=10.0,
        )
        return payload if isinstance(payload, dict) else {}

    def report_applied_config(self, config: dict[str, Any]) -> None:
        """Accuse réception de la configuration appliquée."""
        request_json(
            "POST",
            f"{self._base}/api/boxes/me/config/applied",
            headers=self._auth(),
            body=config,
            timeout=10.0,
        )

    def report_snapshot(self, slug: str) -> None:
        """Signale au backend un snapshot Home Assistant que la box vient de prendre."""
        request_json(
            "POST",
            f"{self._base}/api/boxes/me/snapshots",
            headers=self._auth(),
            body={"slug": slug},
            timeout=10.0,
        )

    def register_ha_token(self, token: str) -> None:
        """Enregistre le jeton d'accès Home Assistant (long-lived) auprès du backend."""
        request_json(
            "POST",
            f"{self._base}/api/boxes/me/ha-token",
            headers=self._auth(),
            body={"token": token},
            timeout=10.0,
        )

    def _auth(self) -> dict[str, str]:
        key = self._api_key()
        if key is None:
            msg = "box non enrolee : aucune cle API"
            raise HttpError(self._base, None, msg)
        return {"Authorization": f"Bearer {key}"}


def _telemetry(state: BoxState) -> dict[str, Any]:
    return {
        "internet": state.internet.value,
        "cloud": state.cloud.value,
        "mesh": state.mesh.value,
        "home_assistant": state.home_assistant.value,
        "zigbee_coordinator": state.zigbee_coordinator.value,
        "zigbee_devices": state.zigbee_devices,
        "ip_address": state.ip_address,
        "hostname": state.hostname,
        "disk_free_percent": state.disk_free_percent,
        "cpu_temperature_c": state.cpu_temperature_c,
    }


class BackendSupport:
    """Port support cable sur le backend (menu « assistance a distance »)."""

    def __init__(self, backend: BackendClient) -> None:
        """Garde le client."""
        self._backend = backend

    def request_session(self) -> None:
        """Demande une session ; un echec est journalise, jamais bloquant."""
        try:
            result = self._backend.request_support()
        except HttpError:
            _LOGGER.exception("demande d'assistance impossible")
            return
        _LOGGER.info("demande d'assistance %s", result.get("id", "?"))


class BackendReporter:
    """Envoie le heartbeat a chaque rafraichissement ; silencieux hors ligne."""

    def __init__(self, backend: BackendClient, api_key: CredentialsProvider) -> None:
        """Ne tente rien tant qu'il n'y a pas de cle."""
        self._backend = backend
        self._api_key = api_key

    def report(self, state: BoxState, error_code: str | None) -> None:
        """Un heartbeat, ou rien si la box n'est pas enrolee / le reseau est coupe."""
        if self._api_key() is None:
            return
        try:
            self._backend.heartbeat(state, error_code)
        except HttpError as exc:
            _LOGGER.warning("heartbeat echoue : %s", exc)


class BackendHaTokenRegistrar:
    """Enregistre le jeton HA de la box une seule fois, une fois la box enrôlée."""

    def __init__(
        self,
        backend: BackendClient,
        is_enrolled: Callable[[], bool],
        token_provider: Callable[[], str | None],
    ) -> None:
        """Garde le client, la sonde d'enrôlement et la source du jeton."""
        self._backend = backend
        self._is_enrolled = is_enrolled
        self._token_provider = token_provider
        self._registered = False

    def register_if_enrolled(self) -> None:
        """Tente d'enregistrer le jeton ; silencieux tant que la box n'est pas enrôlée."""
        if self._registered or not self._is_enrolled():
            return
        token = self._token_provider()
        if token is None:
            return
        try:
            self._backend.register_ha_token(token)
        except HttpError:
            _LOGGER.exception("enregistrement du jeton HA impossible")
            return
        self._registered = True
        _LOGGER.info("jeton HA enregistré")
