"""Ce que l'application attend du monde exterieur, sans savoir comment c'est fait."""

from typing import Protocol

from neo_box.features.status.domain.state import BoxState
from neo_box.shared.keys import Key


class Buttons(Protocol):
    """La face avant : rend la prochaine touche pressee, ou None."""

    def poll(self) -> Key | None:
        """Depile une pression, sans bloquer."""
        ...


class StateProbe(Protocol):
    """Les sondes qui observent la box."""

    def read(self) -> BoxState:
        """Lit l'etat courant (peut prendre quelques secondes)."""
        ...


class EnrollmentStatus(Protocol):
    """Sait si la box est deja rattachee a un client."""

    def is_enrolled(self) -> bool:
        """True une fois les identifiants recus du backend."""
        ...


class Controls(Protocol):
    """Les actions que le menu peut declencher."""

    def permit_join(self) -> None:
        """Ouvre le reseau Zigbee a l'appairage pendant deux minutes."""
        ...

    def request_support_session(self) -> None:
        """Demande au backend d'ouvrir une session d'assistance a distance."""
        ...

    def reboot(self) -> None:
        """Redemarre l'hote."""
        ...


class Clock(Protocol):
    """Le temps, injectable pour les tests."""

    def monotonic(self) -> float:
        """Secondes ecoulees, monotone."""
        ...

    def sleep(self, seconds: float) -> None:
        """Attend."""
        ...
