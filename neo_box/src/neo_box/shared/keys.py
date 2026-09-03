"""Les touches physiques de la box : une croix directionnelle et deux boutons."""

from enum import Enum, auto


class Key(Enum):
    """Une pression sur un bouton de la face avant."""

    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    OK = auto()
    BACK = auto()
