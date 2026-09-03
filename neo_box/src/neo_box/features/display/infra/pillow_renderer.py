"""Rasterisation d'un Frame en image 1 bit, noir sur blanc."""

import qrcode
from PIL import Image, ImageDraw

from neo_box.features.display.infra.fonts import font
from neo_box.shared.drawing import Box, Frame, HLine, Qr, Text
from neo_box.shared.layout import HEIGHT, WIDTH

BLACK = 0
WHITE = 255
THRESHOLD = 128


def qr_matrix(data: str) -> list[list[bool]]:
    """La grille de modules du QR (zone de silence d'un module incluse)."""
    code = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, border=1)
    code.add_data(data)
    code.make(fit=True)
    matrix: list[list[bool]] = code.get_matrix()
    return matrix


def qr_module_pixels(data: str, size: int) -> int:
    """Taille d'un module en pixels une fois le QR ajuste dans une boite de `size` px."""
    return size // len(qr_matrix(data))


def render(frame: Frame) -> Image.Image:
    """Trace toutes les primitives et retourne une image mode '1' de 250 x 122."""
    canvas = Image.new("L", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(canvas)
    for primitive in frame.primitives:
        match primitive:
            case Text(x, y, text, size, inverted):
                draw.text((x, y), text, fill=WHITE if inverted else BLACK, font=font(size))
            case Box(x, y, w, h, filled):
                rect = (x, y, x + w - 1, y + h - 1)
                draw.rectangle(rect, fill=BLACK if filled else None, outline=BLACK)
            case HLine(x, y, w):
                draw.line((x, y, x + w - 1, y), fill=BLACK)
            case Qr(x, y, data, size):
                _draw_qr(draw, x, y, data, size)
    return canvas.point(lambda v: WHITE if v >= THRESHOLD else BLACK).convert("1")


def _draw_qr(draw: ImageDraw.ImageDraw, x: int, y: int, data: str, size: int) -> None:
    matrix = qr_matrix(data)
    scale = size // len(matrix)
    if scale == 0:
        msg = f"QR trop dense pour une boite de {size} px : {len(matrix)} modules"
        raise ValueError(msg)
    offset = (size - scale * len(matrix)) // 2
    for row, cells in enumerate(matrix):
        for col, dark in enumerate(cells):
            if not dark:
                continue
            left = x + offset + col * scale
            top = y + offset + row * scale
            draw.rectangle((left, top, left + scale - 1, top + scale - 1), fill=BLACK)
