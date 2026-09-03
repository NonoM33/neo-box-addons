"""Ce que le backend donne a la box pour rejoindre le mesh, une seule fois."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class MeshCredentials:
    """Serveur de controle, cle pre-auth a usage unique, nom du noeud."""

    login_server: str
    auth_key: str
    hostname: str

    @classmethod
    def from_payload(cls, payload: Any) -> "MeshCredentials | None":  # noqa: ANN401 - JSON libre
        """Lit le bloc `mesh` de la reponse d'annonce ; None s'il est absent ou incomplet."""
        if not isinstance(payload, dict):
            return None
        login_server = payload.get("login_server")
        auth_key = payload.get("auth_key")
        hostname = payload.get("hostname")
        if not (isinstance(login_server, str) and login_server):
            return None
        if not (isinstance(auth_key, str) and auth_key):
            return None
        if not (isinstance(hostname, str) and hostname):
            return None
        return cls(login_server, auth_key, hostname)
