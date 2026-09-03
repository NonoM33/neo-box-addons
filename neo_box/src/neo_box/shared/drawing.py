"""Primitives de dessin : ce qu'un ecran DECRIT, independamment de ce qui le trace.

Le domaine compose des primitives ; l'infrastructure (Pillow, e-ink) les rasterise.
Aucune primitive ne connait Pillow ni l'ecran physique.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Text:
    """Un texte pose a (x, y), coin superieur gauche, dans une taille de police en pixels."""

    x: int
    y: int
    text: str
    size: int
    inverted: bool = False


@dataclass(frozen=True, slots=True)
class Qr:
    """Un QR code carre de `size` pixels, coin superieur gauche a (x, y)."""

    x: int
    y: int
    data: str
    size: int


@dataclass(frozen=True, slots=True)
class Box:
    """Un rectangle, plein (noir) ou en contour."""

    x: int
    y: int
    w: int
    h: int
    filled: bool = False


@dataclass(frozen=True, slots=True)
class HLine:
    """Un trait horizontal d'un pixel d'epaisseur."""

    x: int
    y: int
    w: int


type Primitive = Text | Qr | Box | HLine


@dataclass(frozen=True, slots=True)
class Frame:
    """Une image complete de l'ecran : la liste ordonnee de ce qu'il faut tracer."""

    primitives: tuple[Primitive, ...]
