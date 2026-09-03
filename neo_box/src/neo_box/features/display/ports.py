"""Port d'affichage : ce que l'application attend d'un ecran, quel qu'il soit."""

from typing import Protocol

from neo_box.shared.drawing import Frame


class Display(Protocol):
    """Un ecran capable d'afficher un Frame."""

    def show(self, frame: Frame) -> None:
        """Affiche le frame en entier."""
        ...

    def sleep(self) -> None:
        """Met l'ecran en veille profonde (l'e-ink garde l'image sans courant)."""
        ...
