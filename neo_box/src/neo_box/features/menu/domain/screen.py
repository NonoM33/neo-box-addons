"""L'ecran du menu : la liste, l'entree courante en video inverse."""

from neo_box.features.menu.domain.menu import Menu
from neo_box.shared.drawing import Box, Frame, Primitive, Text
from neo_box.shared.layout import (
    HEADER_HEIGHT,
    HEIGHT,
    MARGIN,
    SIZE_BODY,
    WIDTH,
    TextMeasurer,
    ellipsize,
)
from neo_box.shared.widgets import header

ROW_HEIGHT = 18
ROW_PADDING = 2
VISIBLE_ROWS = (HEIGHT - HEADER_HEIGHT - MARGIN) // ROW_HEIGHT


def menu_screen(menu: Menu, measurer: TextMeasurer) -> Frame:
    """Compose le menu : au plus VISIBLE_ROWS entrees, fenetre glissante autour du curseur."""
    first = max(0, min(menu.cursor - VISIBLE_ROWS + 1, len(menu.items) - VISIBLE_ROWS))
    first = max(first, 0)
    visible = menu.items[first : first + VISIBLE_ROWS]
    primitives: list[Primitive] = [*header("MENU", "OK = choisir", measurer)]
    y = HEADER_HEIGHT + MARGIN
    for index, item in enumerate(visible, start=first):
        selected = index == menu.cursor
        label = ellipsize(item.label, WIDTH - 2 * MARGIN, SIZE_BODY, measurer)
        if selected:
            primitives.append(Box(0, y - ROW_PADDING, WIDTH, ROW_HEIGHT, filled=True))
        primitives.append(Text(MARGIN, y, label, SIZE_BODY, inverted=selected))
        y += ROW_HEIGHT
    return Frame(tuple(primitives))
