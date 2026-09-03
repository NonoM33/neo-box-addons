"""Ce que l'application attend de l'agent mesh."""

from typing import Protocol

from neo_box.features.mesh.domain.credentials import MeshCredentials
from neo_box.features.status.domain.state import Link


class MeshAgent(Protocol):
    """L'agent qui fait rejoindre la box au mesh et dit si elle y est."""

    def join(self, credentials: MeshCredentials) -> None:
        """Rejoint le mesh avec la cle pre-auth (idempotent une fois enrole)."""
        ...

    def status(self) -> Link:
        """UP si la box est connectee au mesh, DOWN sinon, UNKNOWN si l'agent est absent."""
        ...
