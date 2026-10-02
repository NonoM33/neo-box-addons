"""Connexion au WiFi de la maison via NetworkManager (nmcli)."""

import subprocess

from neo_box.features.wifi_setup.domain.wifi import WifiCredentials


class NmcliJoiner:
    """Appelle `nmcli device wifi connect` sur l'hôte."""

    def __init__(self, timeout: float = 120.0) -> None:
        """Garde le délai maximal de connexion."""
        self._timeout = timeout

    def join(self, credentials: WifiCredentials) -> bool:
        """Connecte la box ; True si nmcli a réussi."""
        try:
            result = subprocess.run(  # noqa: S603
                [  # noqa: S607
                    "nmcli",
                    "device",
                    "wifi",
                    "connect",
                    credentials.ssid,
                    "password",
                    credentials.password,
                ],
                check=False,
                capture_output=True,
                timeout=self._timeout,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        else:
            return result.returncode == 0
