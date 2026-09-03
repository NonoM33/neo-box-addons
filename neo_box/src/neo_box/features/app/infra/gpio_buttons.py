"""La croix directionnelle sur GPIO (gpiozero), boutons a la masse avec pull-up interne.

VERIFIE SUR MATERIEL : NON. A valider au premier boot avec les vrais boutons.
"""

from collections import deque
from typing import Any

from neo_box.shared.keys import Key

BOUNCE_SECONDS = 0.05


class GpioButtons:
    """File des pressions, remplie par les callbacks gpiozero, videe par `poll`."""

    def __init__(self, pins: dict[Key, int]) -> None:
        """`pins` : numero BCM de chaque touche."""
        from gpiozero import Button  # noqa: PLC0415 - import materiel differe

        self._queue: deque[Key] = deque()
        self._buttons: list[Any] = []
        for key, pin in pins.items():
            button = Button(pin, pull_up=True, bounce_time=BOUNCE_SECONDS)
            button.when_pressed = self._pressed(key)
            self._buttons.append(button)

    def poll(self) -> Key | None:
        """La plus ancienne pression non traitee."""
        return self._queue.popleft() if self._queue else None

    def _pressed(self, key: Key) -> Any:  # noqa: ANN401 - callback gpiozero non type
        def handler() -> None:
            self._queue.append(key)

        return handler
