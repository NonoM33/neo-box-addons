"""Geometrie de l'ecran et mesure du texte.

L'ecran cible est un Waveshare 2.13" (250 x 122). Toute la mise en page est calculee
a partir des metriques reelles de police (port `TextMeasurer`), jamais devinee :
un chiffre de layout devine est un texte qui deborde chez le client.
"""

from dataclasses import dataclass
from typing import Protocol

from neo_box.shared.drawing import Box, Frame, HLine, Primitive, Qr, Text

WIDTH = 250
HEIGHT = 122
MARGIN = 4
HEADER_HEIGHT = 16
SIZE_SMALL = 11
SIZE_BODY = 13
SIZE_LARGE = 24


class TextMeasurer(Protocol):
    """Mesure un texte dans une taille de police : (largeur, hauteur) en pixels."""

    def measure(self, text: str, size: int) -> tuple[int, int]:
        """Retourne la boite englobante du texte."""
        ...


@dataclass(frozen=True, slots=True)
class Rect:
    """Boite englobante d'une primitive."""

    x: int
    y: int
    w: int
    h: int

    @property
    def right(self) -> int:
        """Bord droit exclusif."""
        return self.x + self.w

    @property
    def bottom(self) -> int:
        """Bord bas exclusif."""
        return self.y + self.h


def bounds(primitive: Primitive, measurer: TextMeasurer) -> Rect:
    """Boite englobante d'une primitive, texte mesure avec la vraie police."""
    match primitive:
        case Text(x, y, text, size, _):
            w, h = measurer.measure(text, size)
            return Rect(x, y, w, h)
        case Qr(x, y, _, size):
            return Rect(x, y, size, size)
        case Box(x, y, w, h, _):
            return Rect(x, y, w, h)
        case HLine(x, y, w):
            return Rect(x, y, w, 1)


def overflowing(frame: Frame, measurer: TextMeasurer) -> tuple[Primitive, ...]:
    """Les primitives qui sortent de l'ecran. Vide = la mise en page tient."""
    outside: list[Primitive] = []
    for primitive in frame.primitives:
        rect = bounds(primitive, measurer)
        if rect.x < 0 or rect.y < 0 or rect.right > WIDTH or rect.bottom > HEIGHT:
            outside.append(primitive)
    return tuple(outside)


def wrap(text: str, max_width: int, size: int, measurer: TextMeasurer) -> tuple[str, ...]:
    """Coupe un texte en lignes qui tiennent dans `max_width`, sur les espaces."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = word if not current else f"{current} {word}"
        if measurer.measure(candidate, size)[0] <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
    if current:
        lines.append(current)
    return tuple(lines)


def ellipsize(text: str, max_width: int, size: int, measurer: TextMeasurer) -> str:
    """Raccourcit un texte avec `...` pour qu'il tienne dans `max_width`."""
    if measurer.measure(text, size)[0] <= max_width:
        return text
    kept = text
    while kept and measurer.measure(kept + "...", size)[0] > max_width:
        kept = kept[:-1]
    return kept.rstrip() + "..."


def right_aligned(text: str, right: int, y: int, size: int, measurer: TextMeasurer) -> Text:
    """Un texte dont le bord droit est cale sur `right`."""
    w, _ = measurer.measure(text, size)
    return Text(right - w, y, text, size)
