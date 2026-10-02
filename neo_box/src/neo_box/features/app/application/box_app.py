"""La machine a etats de la box : quel ecran, et que fait chaque touche.

Pure : aucune entree-sortie ici. Les touches produisent au plus une `Command`,
que l'execution (`runtime`) traduit en appels reels.
"""

from dataclasses import dataclass, field
from enum import Enum, auto

from neo_box.features.enrollment.domain.screen import enrollment_screen
from neo_box.features.enrollment.domain.token import ProvisioningToken
from neo_box.features.errors.domain.screen import error_screen
from neo_box.features.menu.domain.menu import Menu, MenuAction
from neo_box.features.menu.domain.screen import menu_screen
from neo_box.features.pairing.domain.code import PairingCode
from neo_box.features.pairing.domain.screen import pairing_screen
from neo_box.features.status.domain.diagnosis import diagnose
from neo_box.features.status.domain.screen import network_screen, status_screen
from neo_box.features.status.domain.state import BoxState
from neo_box.shared.drawing import Frame
from neo_box.shared.keys import Key
from neo_box.shared.layout import TextMeasurer


class Mode(Enum):
    """L'ecran courant."""

    ENROLLING = auto()
    HOME = auto()
    MENU = auto()
    NETWORK = auto()
    PAIRING = auto()


class Command(Enum):
    """Un effet de bord demande par l'utilisateur, a executer hors du domaine."""

    SHOW_PAIRING = auto()
    PERMIT_JOIN = auto()
    SUPPORT_SESSION = auto()
    REBOOT = auto()


_COMMANDS = {
    MenuAction.SHOW_PAIRING: Command.SHOW_PAIRING,
    MenuAction.PERMIT_JOIN: Command.PERMIT_JOIN,
    MenuAction.SUPPORT_SESSION: Command.SUPPORT_SESSION,
    MenuAction.REBOOT: Command.REBOOT,
}


@dataclass
class BoxApp:
    """L'etat de l'interface : mode, menu, dernier etat observe."""

    help_base_url: str
    token: ProvisioningToken | None = None
    pairing_code: PairingCode | None = None
    state: BoxState = field(default_factory=BoxState)
    mode: Mode = field(init=False)
    menu: Menu = field(default_factory=Menu)

    def __post_init__(self) -> None:
        """Une box qui porte encore son jeton n'est pas enrolee : elle demarre sur le QR."""
        self.mode = Mode.ENROLLING if self.token is not None else Mode.HOME

    def enrolled(self) -> None:
        """Le backend a accepte le jeton : on quitte l'ecran d'enrolement pour de bon."""
        self.token = None
        if self.mode is Mode.ENROLLING:
            self.mode = Mode.HOME

    def show_pairing(self, code: PairingCode | None) -> None:
        """Affiche le code d'appairage recu, ou revient au statut si aucun."""
        self.pairing_code = code
        self.mode = Mode.PAIRING if code is not None else Mode.HOME

    def update_state(self, state: BoxState) -> None:
        """Nouvelle photographie des sondes."""
        self.state = state

    def on_key(self, key: Key) -> Command | None:
        """Applique une touche ; rend la commande a executer, s'il y en a une."""
        match self.mode:
            case Mode.ENROLLING:
                return None
            case Mode.HOME:
                if key is Key.OK:
                    self.menu = Menu()
                    self.mode = Mode.MENU
                return None
            case Mode.MENU:
                return self._on_menu_key(key)
            case Mode.NETWORK:
                self.mode = Mode.HOME
                return None
            case Mode.PAIRING:
                self.mode = Mode.HOME
                return None

    def frame(self, measurer: TextMeasurer) -> Frame:
        """L'ecran a afficher pour l'etat courant."""
        match self.mode:
            case Mode.ENROLLING:
                if self.token is None:
                    msg = "mode ENROLLING sans jeton"
                    raise RuntimeError(msg)
                return enrollment_screen(self.token, self.state.version, measurer)
            case Mode.MENU:
                return menu_screen(self.menu, measurer)
            case Mode.NETWORK:
                return network_screen(self.state, measurer)
            case Mode.PAIRING:
                if self.pairing_code is None:
                    msg = "mode PAIRING sans code"
                    raise RuntimeError(msg)
                return pairing_screen(self.pairing_code, self.state.version, measurer)
            case Mode.HOME:
                error = diagnose(self.state)
                if error is not None:
                    return error_screen(error, self.help_base_url, measurer)
                return status_screen(self.state, measurer)

    def _on_menu_key(self, key: Key) -> Command | None:
        if key in (Key.BACK, Key.LEFT):
            self.mode = Mode.HOME
            return None
        if key is not Key.OK:
            self.menu = self.menu.move(key)
            return None
        action = self.menu.selected.action
        if action is MenuAction.SHOW_NETWORK:
            self.mode = Mode.NETWORK
        else:
            self.mode = Mode.HOME
        return _COMMANDS.get(action)
