"""L'enrolement vu de la box : s'annoncer jusqu'a recevoir sa cle, puis la garder."""

import logging
from typing import Protocol

from neo_box.features.app.infra.http import HttpError
from neo_box.features.enrollment.domain.token import ProvisioningToken
from neo_box.features.mesh.domain.credentials import MeshCredentials
from neo_box.features.mesh.ports import MeshAgent

_LOGGER = logging.getLogger(__name__)


class CredentialsStore(Protocol):
    """Ou vivent le jeton et les identifiants."""

    def token(self) -> ProvisioningToken:
        """Le jeton de cette box."""
        ...

    def is_enrolled(self) -> bool:
        """True si des identifiants sont deja la."""
        ...

    def save_credentials(
        self, api_key: str, box_id: str, mesh: MeshCredentials | None = None
    ) -> None:
        """Ecrit les identifiants recus."""
        ...

    def mesh_credentials(self) -> MeshCredentials | None:
        """La cle mesh gardee, ou None."""
        ...


class Announcer(Protocol):
    """Ce qu'il faut du backend : une annonce."""

    def announce(self, token: str, hardware_id: str, version: str) -> dict[str, object]:
        """Retourne la reponse JSON du backend."""
        ...


class EnrollmentService:
    """Implemente `EnrollmentStatus` : chaque appel tente une annonce tant qu'on n'a rien."""

    def __init__(
        self,
        store: CredentialsStore,
        backend: Announcer,
        mesh: MeshAgent,
        hardware_id: str,
        version: str,
    ) -> None:
        """Garde de quoi s'annoncer et rejoindre le mesh."""
        self._store = store
        self._backend = backend
        self._mesh = mesh
        self._hardware_id = hardware_id
        self._version = version

    def is_enrolled(self) -> bool:
        """True des que les identifiants sont en place (deja la, ou recus a l'instant)."""
        if self._store.is_enrolled():
            self._join_mesh()
            return True
        try:
            reply = self._backend.announce(
                self._store.token().value, self._hardware_id, self._version
            )
        except HttpError as exc:
            _LOGGER.warning("annonce impossible : %s", exc)
            return False
        api_key, box_id = reply.get("api_key"), reply.get("box_id")
        if (
            reply.get("status") == "claimed"
            and isinstance(api_key, str)
            and isinstance(box_id, str)
        ):
            mesh = MeshCredentials.from_payload(reply.get("mesh"))
            self._store.save_credentials(api_key, box_id, mesh)
            _LOGGER.info("box enrolee : %s", box_id)
            self._join_mesh()
            return True
        _LOGGER.info("annonce : %s", reply.get("status", "?"))
        return False

    def _join_mesh(self) -> None:
        """Rejoint le mesh si on a une cle ; l'agent est idempotent (cle a usage unique)."""
        credentials = self._store.mesh_credentials()
        if credentials is not None:
            self._mesh.join(credentials)
