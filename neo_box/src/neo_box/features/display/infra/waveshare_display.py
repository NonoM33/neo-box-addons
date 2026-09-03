"""Ecran e-ink Waveshare 2.13" (V4) sur le bus SPI du Raspberry Pi.

VERIFIE SUR MATERIEL : NON. Ecrit d'apres la bibliotheque officielle `waveshare_epd`
(module `epd2in13_V4`) ; a valider des reception de l'ecran avant toute livraison.
Le driver attend une image portrait 122 x 250 et retourne lui-meme une image
paysage 250 x 122 dans `getbuffer`.
"""

from typing import Any

from neo_box.features.display.infra.pillow_renderer import render
from neo_box.shared.drawing import Frame


class WaveshareDisplay:
    """Pilote l'e-ink : rafraichissement complet a chaque frame, veille entre deux."""

    def __init__(self, epd: Any) -> None:  # noqa: ANN401 - driver C sans typage
        """Recoit une instance `epd2in13_V4.EPD()` deja construite."""
        self._epd = epd
        self._awake = False

    @classmethod
    def open(cls) -> "WaveshareDisplay":
        """Charge le driver Waveshare (present uniquement dans l'image de l'add-on)."""
        from waveshare_epd import epd2in13_V4  # noqa: PLC0415 - import materiel differe

        return cls(epd2in13_V4.EPD())

    def show(self, frame: Frame) -> None:
        """Reveille l'ecran, affiche le frame entier, puis le rendort."""
        if not self._awake:
            self._epd.init()
            self._awake = True
        self._epd.display(self._epd.getbuffer(render(frame)))
        self.sleep()

    def sleep(self) -> None:
        """Veille profonde : l'image reste affichee sans consommer."""
        if self._awake:
            self._epd.sleep()
            self._awake = False
