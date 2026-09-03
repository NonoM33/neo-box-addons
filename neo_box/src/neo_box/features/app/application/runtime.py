"""L'execution : boucle qui relie touches, sondes, machine a etats et ecran.

L'e-ink est lent et s'use a chaque rafraichissement : on n'affiche que quand le
frame change, et on ne relit les sondes qu'a intervalle regulier.
"""

import logging
from dataclasses import dataclass, field

from neo_box.features.app.application.box_app import BoxApp, Command
from neo_box.features.app.application.ports import (
    Buttons,
    Clock,
    Controls,
    EnrollmentStatus,
    StateProbe,
)
from neo_box.features.display.ports import Display
from neo_box.shared.drawing import Frame
from neo_box.shared.layout import TextMeasurer

_LOGGER = logging.getLogger(__name__)


@dataclass
class Runtime:
    """Un pas = lire les touches, rafraichir l'etat si c'est l'heure, afficher si ca change."""

    app: BoxApp
    display: Display
    buttons: Buttons
    probe: StateProbe
    enrollment: EnrollmentStatus
    controls: Controls
    clock: Clock
    measurer: TextMeasurer
    refresh_seconds: float = 30.0
    poll_seconds: float = 0.05
    _last_frame: Frame | None = field(default=None, init=False)
    _last_refresh: float | None = field(default=None, init=False)

    def step(self) -> None:
        """Un tour de boucle, sans attente."""
        key = self.buttons.poll()
        if key is not None:
            command = self.app.on_key(key)
            if command is not None:
                self._execute(command)
        if self._refresh_due():
            self._refresh()
        self._show_if_changed()

    def run(self) -> None:
        """Boucle sans fin (Ctrl-C ou signal pour sortir)."""
        while True:
            self.step()
            self.clock.sleep(self.poll_seconds)

    def _refresh_due(self) -> bool:
        now = self.clock.monotonic()
        if self._last_refresh is None or now - self._last_refresh >= self.refresh_seconds:
            self._last_refresh = now
            return True
        return False

    def _refresh(self) -> None:
        self.app.update_state(self.probe.read())
        if self.app.token is not None and self.enrollment.is_enrolled():
            self.app.enrolled()

    def _show_if_changed(self) -> None:
        frame = self.app.frame(self.measurer)
        if frame != self._last_frame:
            self.display.show(frame)
            self._last_frame = frame

    def _execute(self, command: Command) -> None:
        _LOGGER.info("commande %s", command.name)
        match command:
            case Command.PERMIT_JOIN:
                self.controls.permit_join()
            case Command.SUPPORT_SESSION:
                self.controls.request_support_session()
            case Command.REBOOT:
                self.controls.reboot()
