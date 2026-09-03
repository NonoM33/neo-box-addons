"""L'ecran d'erreur : le code en grand, le libelle, et un QR vers la fiche d'aide."""

from neo_box.features.errors.domain.catalogue import ErrorCode, help_url
from neo_box.shared.drawing import Frame, Primitive, Qr, Text
from neo_box.shared.layout import (
    HEADER_HEIGHT,
    HEIGHT,
    MARGIN,
    SIZE_BODY,
    SIZE_LARGE,
    SIZE_SMALL,
    WIDTH,
    TextMeasurer,
    wrap,
)
from neo_box.shared.widgets import header

QR_SIZE = HEIGHT - HEADER_HEIGHT - 2 * MARGIN
LINE_GAP = 2


def error_screen(error: ErrorCode, help_base_url: str, measurer: TextMeasurer) -> Frame:
    """Compose l'ecran d'erreur : QR a gauche, code et libelle a droite."""
    column_x = MARGIN + QR_SIZE + 2 * MARGIN
    column_w = WIDTH - column_x - MARGIN
    primitives: list[Primitive] = [
        *header("ERREUR", "OK = menu", measurer),
        Qr(MARGIN, HEADER_HEIGHT + MARGIN, help_url(error, help_base_url), QR_SIZE),
    ]
    y = HEADER_HEIGHT + MARGIN
    primitives.append(Text(column_x, y, error.code, SIZE_LARGE))
    y += measurer.measure(error.code, SIZE_LARGE)[1] + LINE_GAP
    for line in wrap(error.label, column_w, SIZE_BODY, measurer):
        primitives.append(Text(column_x, y, line, SIZE_BODY))
        y += measurer.measure(line, SIZE_BODY)[1] + LINE_GAP
    hint = "Scannez pour l'aide"
    hint_h = measurer.measure(hint, SIZE_SMALL)[1]
    primitives.append(Text(column_x, HEIGHT - MARGIN - hint_h, hint, SIZE_SMALL))
    return Frame(tuple(primitives))
