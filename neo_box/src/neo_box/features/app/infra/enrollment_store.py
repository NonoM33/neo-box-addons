"""Ou la box garde son jeton et, une fois enrolee, ses identifiants."""

import json
from dataclasses import dataclass
from pathlib import Path

from neo_box.features.enrollment.domain.token import ProvisioningToken
from neo_box.features.mesh.domain.credentials import MeshCredentials


@dataclass(frozen=True)
class FileEnrollmentStore:
    """Deux fichiers dans /data : le jeton (genere au premier boot) et les identifiants."""

    directory: Path

    @property
    def token_path(self) -> Path:
        """Le jeton de provisioning, en clair (il n'a de valeur qu'avant l'enrolement)."""
        return self.directory / "provisioning_token"

    @property
    def credentials_path(self) -> Path:
        """Les identifiants recus du backend ; leur presence vaut enrolement."""
        return self.directory / "credentials.json"

    def token(self) -> ProvisioningToken:
        """Le jeton de cette box, cree au premier appel et stable ensuite."""
        if self.token_path.exists():
            return ProvisioningToken.parse(self.token_path.read_text())
        token = ProvisioningToken.generate()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(token.value)
        return token

    def is_enrolled(self) -> bool:
        """True si des identifiants lisibles sont presents."""
        return self.api_key() is not None

    def api_key(self) -> str | None:
        """La cle API, ou None tant que la box n'est pas enrolee."""
        try:
            data = json.loads(self.credentials_path.read_text())
        except (OSError, ValueError):
            return None
        key = data.get("api_key") if isinstance(data, dict) else None
        return key if isinstance(key, str) and key else None

    def save_credentials(
        self, api_key: str, box_id: str, mesh: MeshCredentials | None = None
    ) -> None:
        """Ecrit les identifiants (et la cle mesh) ; le fichier n'est lisible que par le daemon."""
        self.directory.mkdir(parents=True, exist_ok=True)
        payload: dict[str, object] = {"api_key": api_key, "box_id": box_id}
        if mesh is not None:
            payload["mesh"] = {
                "login_server": mesh.login_server,
                "auth_key": mesh.auth_key,
                "hostname": mesh.hostname,
            }
        self.credentials_path.write_text(json.dumps(payload))
        self.credentials_path.chmod(0o600)

    def mesh_credentials(self) -> MeshCredentials | None:
        """La cle mesh recue a l'enrolement, ou None."""
        try:
            data = json.loads(self.credentials_path.read_text())
        except (OSError, ValueError):
            return None
        return MeshCredentials.from_payload(data.get("mesh")) if isinstance(data, dict) else None
