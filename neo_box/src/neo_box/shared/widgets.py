"""Composants de mise en page partages par tous les ecrans."""

from neo_box.shared.drawing import Box, Primitive, Text
from neo_box.shared.layout import (
    HEADER_HEIGHT,
    MARGIN,
    SIZE_SMALL,
    WIDTH,
    TextMeasurer,
)


def header(title: str, right: str, measurer: TextMeasurer) -> tuple[Primitive, ...]:
    """Bandeau inverse en haut de l'ecran : titre a gauche, information a droite."""
    _, text_h = measurer.measure(title, SIZE_SMALL)
    y = (HEADER_HEIGHT - text_h) // 2
    right_w, _ = measurer.measure(right, SIZE_SMALL)
    return (
        Box(0, 0, WIDTH, HEADER_HEIGHT, filled=True),
        Text(MARGIN, y, title, SIZE_SMALL, inverted=True),
        Text(WIDTH - MARGIN - right_w, y, right, SIZE_SMALL, inverted=True),
    )
