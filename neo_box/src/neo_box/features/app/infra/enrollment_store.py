"""Ou la box garde son jeton et, une fois enrolee, ses identifiants."""

import json
from dataclasses import dataclass
from pathlib import Path

from neo_box.features.enrollment.domain.token import ProvisioningToken


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

    def save_credentials(self, api_key: str, box_id: str) -> None:
        """Ecrit les identifiants ; le fichier n'est lisible que par le daemon."""
        self.directory.mkdir(parents=True, exist_ok=True)
        self.credentials_path.write_text(json.dumps({"api_key": api_key, "box_id": box_id}))
        self.credentials_path.chmod(0o600)
