"""Le menu et sa navigation : une valeur immuable, une touche donne un nouveau menu."""

from dataclasses import dataclass, replace
from enum import Enum, auto

from neo_box.shared.keys import Key


class MenuAction(Enum):
    """Ce qu'une entree de menu declenche quand on la valide."""

    PERMIT_JOIN = auto()
    SUPPORT_SESSION = auto()
    SHOW_NETWORK = auto()
    REBOOT = auto()
    BACK = auto()


@dataclass(frozen=True, slots=True)
class MenuItem:
    """Une entree de menu : son action et son libelle."""

    action: MenuAction
    label: str


MAIN_ITEMS: tuple[MenuItem, ...] = (
    MenuItem(MenuAction.PERMIT_JOIN, "Appairer un appareil Zigbee"),
    MenuItem(MenuAction.SUPPORT_SESSION, "Ouvrir l'assistance a distance"),
    MenuItem(MenuAction.SHOW_NETWORK, "Reseau"),
    MenuItem(MenuAction.REBOOT, "Redemarrer la box"),
    MenuItem(MenuAction.BACK, "Retour"),
)


@dataclass(frozen=True, slots=True)
class Menu:
    """Une liste d'entrees et la position du curseur."""

    items: tuple[MenuItem, ...] = MAIN_ITEMS
    cursor: int = 0

    @property
    def selected(self) -> MenuItem:
        """L'entree sous le curseur."""
        return self.items[self.cursor]

    def move(self, key: Key) -> "Menu":
        """Deplace le curseur (haut/bas, en boucle) ; toute autre touche ne change rien."""
        if key is Key.UP:
            return replace(self, cursor=(self.cursor - 1) % len(self.items))
        if key is Key.DOWN:
            return replace(self, cursor=(self.cursor + 1) % len(self.items))
        return self
