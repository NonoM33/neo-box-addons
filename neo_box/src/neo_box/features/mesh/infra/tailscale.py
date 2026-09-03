"""Tailscale embarque dans l'add-on, en mode userspace (pas de TUN, pas de NET_ADMIN).

L'add-on partage le reseau de l'hote (`host_network: true`) : un client du mesh qui
joint l'adresse de la box sur le port 8123 tombe sur Home Assistant.
VERIFIE SUR MATERIEL : NON.
"""

import json
import logging
import subprocess
from collections.abc import Callable
from pathlib import Path

from neo_box.features.mesh.domain.credentials import MeshCredentials
from neo_box.features.status.domain.state import Link

_LOGGER = logging.getLogger(__name__)

Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    """Execute une commande sans shell, en capturant la sortie."""
    return subprocess.run(argv, capture_output=True, text=True, check=False, timeout=60)  # noqa: S603


class TailscaleAgent:
    """Pilote `tailscaled` (lance par run.sh) via la commande `tailscale`."""

    def __init__(self, state_dir: Path, runner: Runner = run) -> None:
        """`state_dir` garde le marqueur d'enrolement ; `runner` s'injecte pour les tests."""
        self._state_dir = state_dir
        self._runner = runner

    @property
    def joined_marker(self) -> Path:
        """Present une fois `tailscale up` reussi : on ne rejoue pas la cle (usage unique)."""
        return self._state_dir / "mesh_joined"

    def join(self, credentials: MeshCredentials) -> None:
        """`tailscale up` avec la cle pre-auth ; ne fait rien si deja fait."""
        if self.joined_marker.exists():
            return
        result = self._runner(
            [
                "tailscale",
                "up",
                f"--login-server={credentials.login_server}",
                f"--authkey={credentials.auth_key}",
                f"--hostname={credentials.hostname}",
                "--accept-dns=false",
                "--accept-routes=false",
            ]
        )
        if result.returncode != 0:
            _LOGGER.warning("tailscale up a echoue : %s", result.stderr.strip())
            return
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self.joined_marker.write_text(credentials.hostname)
        _LOGGER.info("mesh rejoint : %s", credentials.hostname)

    def status(self) -> Link:
        """Lit `tailscale status --json` : BackendState Running = connecte."""
        try:
            result = self._runner(["tailscale", "status", "--json"])
        except (OSError, subprocess.SubprocessError):
            return Link.UNKNOWN
        if result.returncode != 0:
            return Link.DOWN if self.joined_marker.exists() else Link.UNKNOWN
        try:
            state = json.loads(result.stdout).get("BackendState")
        except (ValueError, AttributeError):
            return Link.UNKNOWN
        return Link.UP if state == "Running" else Link.DOWN


class NoMeshAgent:
    """Pas d'agent (simulateur, developpement) : le mesh reste inconnu."""

    def join(self, credentials: MeshCredentials) -> None:
        """Rien : on note seulement ce qu'on aurait fait."""
        _LOGGER.info(
            "mesh (simule) : rejoindrait %s en %s", credentials.login_server, credentials.hostname
        )

    def status(self) -> Link:
        """Inconnu."""
        return Link.UNKNOWN
