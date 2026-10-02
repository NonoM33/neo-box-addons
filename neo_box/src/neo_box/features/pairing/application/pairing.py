"""Fournir un code d'appairage client frais, recu du backend."""

import logging
from typing import Any, Protocol

from neo_box.features.app.infra.http import HttpError
from neo_box.features.pairing.domain.code import InvalidPairingCodeError, PairingCode

_LOGGER = logging.getLogger(__name__)


class PairingProvider(Protocol):
    """Sait obtenir un code d'appairage a afficher."""

    def fetch_code(self) -> PairingCode | None:
        """Un code frais, ou None si le backend est injoignable ou muet."""
        ...


class PairingBackend(Protocol):
    """Ce qu'il faut du backend : une demande de code d'appairage."""

    def pairing_code(self) -> dict[str, Any]:
        """Reponse JSON de `POST /api/boxes/me/pairing-code`."""
        ...


class BackendPairing:
    """Adapter : demande le code au backend et le valide."""

    def __init__(self, backend: PairingBackend) -> None:
        """Garde le client backend."""
        self._backend = backend

    def fetch_code(self) -> PairingCode | None:
        """Un code frais ; un echec reseau ou un code illisible rend None, jamais une exception."""
        try:
            reply = self._backend.pairing_code()
        except HttpError:
            _LOGGER.exception("code d'appairage impossible")
            return None
        code = reply.get("pairingCode") if isinstance(reply, dict) else None
        if not isinstance(code, str):
            return None
        try:
            return PairingCode.parse(code)
        except InvalidPairingCodeError:
            _LOGGER.warning("code d'appairage illisible : %r", code)
            return None


class NoPairing:
    """Aucun backend : pas de code d'appairage."""

    def fetch_code(self) -> PairingCode | None:
        """Rien."""
        return None
