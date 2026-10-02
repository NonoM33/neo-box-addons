"""Orchestration du premier branchement de la box.

Sans Internet, ouvrir un point d'accès, recueillir le WiFi de la maison, s'y
connecter, puis refermer le point d'accès.
"""

import logging
from typing import Protocol

from neo_box.features.wifi_setup.domain.wifi import WifiCredentials

_LOGGER = logging.getLogger(__name__)


class Internet(Protocol):
    """Sait si la box a accès à Internet."""

    def online(self) -> bool:
        """True si Internet répond."""
        ...


class AccessPoint(Protocol):
    """Le point d'accès WiFi temporaire qui accueille l'installateur."""

    def start(self) -> None:
        """Allume le point d'accès."""
        ...

    def stop(self) -> None:
        """Éteint le point d'accès."""
        ...


class Portal(Protocol):
    """Le portail captif qui demande le WiFi de la maison."""

    def collect(self) -> WifiCredentials | None:
        """Bloque jusqu'à recevoir des identifiants, ou None si abandonné."""
        ...


class WifiJoiner(Protocol):
    """Sait connecter la box à un réseau WiFi."""

    def join(self, credentials: WifiCredentials) -> bool:
        """Connecte la box ; True si la commande a réussi."""
        ...


class Clock(Protocol):
    """Le temps, injectable pour les tests."""

    def sleep(self, seconds: float) -> None:
        """Attend."""
        ...


class WifiSetup:
    """Scénario : pas d'Internet → AP + portail → join → Internet (ou échec)."""

    def __init__(  # noqa: PLR0913, PLR0917
        self,
        access_point: AccessPoint,
        portal: Portal,
        joiner: WifiJoiner,
        internet: Internet,
        clock: Clock,
        attempts: int = 10,
        delay: float = 3.0,
    ) -> None:
        """Garde les adaptateurs et le rythme de la vérification finale."""
        self._ap = access_point
        self._portal = portal
        self._joiner = joiner
        self._internet = internet
        self._clock = clock
        self._attempts = attempts
        self._delay = delay

    def run(self) -> bool:
        """Tente d'obtenir Internet ; True si la box est en ligne à la fin."""
        if self._internet.online():
            return True
        _LOGGER.info("pas d'Internet : ouverture du point d'accès WiFi")
        self._ap.start()
        try:
            credentials = self._portal.collect()
            if credentials is None:
                _LOGGER.warning("aucun identifiant WiFi reçu")
                return False
            if not self._joiner.join(credentials):
                _LOGGER.error("échec de la connexion au WiFi")
                return False
            return self._wait_for_internet()
        finally:
            self._ap.stop()

    def _wait_for_internet(self) -> bool:
        for _ in range(self._attempts):
            if self._internet.online():
                return True
            self._clock.sleep(self._delay)
        return False
