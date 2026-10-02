"""Point d'accès WiFi temporaire : hostapd + dnsmasq, pilotés en sous-processus.

VERIFIE SUR MATERIEL : NON. Les chemins de config et les commandes sont écrits
pour HA OS sur Raspberry Pi ; à valider au premier boot.
"""

import subprocess
from pathlib import Path

_CONFIG_DIR = Path("/tmp/neo-wifi")  # noqa: S108


class HostapdAp:
    """Émet un AP sans mot de passe (portail captif) sur le WiFi du Pi."""

    def __init__(self, ssid: str = "NeoBox-Setup", interface: str = "wlan0") -> None:
        """Garde le SSID et l'interface WiFi."""
        self._ssid = ssid
        self._interface = interface
        self._hostapd: subprocess.Popen[bytes] | None = None
        self._dnsmasq: subprocess.Popen[bytes] | None = None

    def start(self) -> None:
        """Écrit les configs et lance hostapd + dnsmasq."""
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        hostapd_conf = _CONFIG_DIR / "hostapd.conf"
        hostapd_conf.write_text(
            f"interface={self._interface}\n"
            f"driver=nl80211\n"
            f"ssid={self._ssid}\n"
            "hw_mode=g\nchannel=6\n"
            "wmm_enabled=0\nmacaddr_acl=0\nauth_algs=1\nignore_broadcast_ssid=0\n"
        )
        dnsmasq_conf = _CONFIG_DIR / "dnsmasq.conf"
        dnsmasq_conf.write_text(
            f"interface={self._interface}\n"
            "bind-interfaces\n"
            "dhcp-range=10.10.0.10,10.10.0.100,12h\n"
            "dhcp-option=3,10.10.0.1\n"
            "address=/#/10.10.0.1\n"
        )
        self._hostapd = subprocess.Popen(  # noqa: S603
            ["hostapd", str(hostapd_conf)],  # noqa: S607
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._dnsmasq = subprocess.Popen(  # noqa: S603
            ["dnsmasq", "-C", str(dnsmasq_conf), "--no-resolv"],  # noqa: S607
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop(self) -> None:
        """Termine hostapd et dnsmasq, sans erreur s'ils n'ont jamais démarré."""
        for process in (self._hostapd, self._dnsmasq):
            if process is not None:
                process.terminate()
        self._hostapd = None
        self._dnsmasq = None
