"""Le vocabulaire du réglage WiFi : les identifiants de la maison."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WifiCredentials:
    """Le réseau WiFi auquel la box doit se connecter."""

    ssid: str
    password: str
