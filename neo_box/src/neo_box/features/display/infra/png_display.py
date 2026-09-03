"""Ecran de developpement : chaque affichage ecrit un PNG sur disque."""

from pathlib import Path

from neo_box.features.display.infra.pillow_renderer import render
from neo_box.shared.drawing import Frame


class PngDisplay:
    """Ecrit `latest.png` a chaque `show`, plus un historique numerote."""

    def __init__(self, directory: Path) -> None:
        """Cree le dossier de sortie s'il n'existe pas."""
        self._directory = directory
        self._directory.mkdir(parents=True, exist_ok=True)
        self._counter = 0

    def show(self, frame: Frame) -> None:
        """Rasterise et ecrit le frame."""
        image = render(frame)
        image.save(self._directory / "latest.png")
        image.save(self._directory / f"{self._counter:04d}.png")
        self._counter += 1

    def sleep(self) -> None:
        """Rien a faire : un fichier ne consomme pas."""
