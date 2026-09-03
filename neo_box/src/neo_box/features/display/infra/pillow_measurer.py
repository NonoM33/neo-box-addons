"""Mesure du texte avec les VRAIES metriques de la police rendue."""

from neo_box.features.display.infra.fonts import font


class PillowTextMeasurer:
    """Implemente `TextMeasurer` avec la police reellement tracee a l'ecran."""

    def measure(self, text: str, size: int) -> tuple[int, int]:
        """Largeur et hauteur occupees depuis l'origine de trace (x, y)."""
        _, _, right, bottom = font(size).getbbox(text)
        return int(right), int(bottom)
