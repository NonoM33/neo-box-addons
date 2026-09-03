"""L'ecran d'enrolement : le QR a scanner et le code a recopier en cas d'echec."""

from neo_box.features.enrollment.domain.token import ProvisioningToken
from neo_box.shared.drawing import Frame, Primitive, Qr, Text
from neo_box.shared.layout import (
    HEADER_HEIGHT,
    HEIGHT,
    MARGIN,
    SIZE_BODY,
    SIZE_SMALL,
    WIDTH,
    TextMeasurer,
    wrap,
)
from neo_box.shared.widgets import header

QR_SIZE = HEIGHT - HEADER_HEIGHT - 2 * MARGIN
LINE_GAP = 2
INSTRUCTION = "Scannez ce code avec l'app Neo installateur"


def enrollment_screen(token: ProvisioningToken, version: str, measurer: TextMeasurer) -> Frame:
    """Compose l'ecran d'enrolement : QR a gauche, consigne et code a droite."""
    column_x = MARGIN + QR_SIZE + 2 * MARGIN
    column_w = WIDTH - column_x - MARGIN
    primitives: list[Primitive] = [
        *header("INSTALLATION", version, measurer),
        Qr(MARGIN, HEADER_HEIGHT + MARGIN, token.qr_payload, QR_SIZE),
    ]
    y = HEADER_HEIGHT + MARGIN
    for line in wrap(INSTRUCTION, column_w, SIZE_BODY, measurer):
        primitives.append(Text(column_x, y, line, SIZE_BODY))
        y += measurer.measure(line, SIZE_BODY)[1] + LINE_GAP
    code_lines = _split_code(token.display, column_w, measurer)
    line_h = measurer.measure(code_lines[0], SIZE_SMALL)[1]
    y = HEIGHT - MARGIN - len(code_lines) * (line_h + LINE_GAP)
    for line in code_lines:
        primitives.append(Text(column_x, y, line, SIZE_SMALL))
        y += line_h + LINE_GAP
    return Frame(tuple(primitives))


def _split_code(display: str, max_width: int, measurer: TextMeasurer) -> tuple[str, ...]:
    """Le code groupe, coupe entre deux groupes pour tenir dans la colonne."""
    lines: list[str] = []
    current = ""
    for group in display.split("-"):
        candidate = group if not current else f"{current}-{group}"
        if measurer.measure(candidate, SIZE_SMALL)[0] <= max_width:
            current = candidate
            continue
        lines.append(current)
        current = group
    lines.append(current)
    return tuple(lines)
