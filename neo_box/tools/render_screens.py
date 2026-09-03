"""Rend TOUS les ecrans de la box en PNG et une planche contact agrandie.

Regarder la planche avant de livrer : un test de layout prouve que rien ne deborde,
pas qu'un ecran est lisible.
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from neo_box.features.display.infra.fonts import font
from neo_box.features.display.infra.pillow_measurer import PillowTextMeasurer
from neo_box.features.display.infra.pillow_renderer import render
from neo_box.features.enrollment.domain.screen import enrollment_screen
from neo_box.features.enrollment.domain.token import ProvisioningToken
from neo_box.features.errors.domain.catalogue import CATALOGUE
from neo_box.features.errors.domain.screen import error_screen
from neo_box.features.menu.domain.menu import Menu
from neo_box.features.menu.domain.screen import menu_screen
from neo_box.features.status.domain.screen import network_screen, status_screen
from neo_box.features.status.domain.state import BoxState, HaHealth, Link
from neo_box.shared.drawing import Frame
from neo_box.shared.layout import HEIGHT, WIDTH

SCALE = 2
COLUMNS = 3
GUTTER = 12
LABEL_HEIGHT = 18
HELP_URL = "https://neo-domotique.fr"

HEALTHY = BoxState(
    internet=Link.UP,
    cloud=Link.UP,
    mesh=Link.UP,
    home_assistant=HaHealth.RUNNING,
    zigbee_coordinator=Link.UP,
    zigbee_devices=12,
    ip_address="192.168.1.42",
    hostname="neo-box-a1b2c3",
    version="v0.1.0",
    disk_free_percent=61,
    cpu_temperature_c=48.5,
)
BOOTING = BoxState(version="v0.1.0", hostname="neo-box-a1b2c3")


def screens() -> list[tuple[str, Frame]]:
    """Chaque ecran nomme, dans l'ordre ou l'installateur les rencontre."""
    measurer = PillowTextMeasurer()
    token = ProvisioningToken.parse("7K3M-9PQR-2STV-WXYZ-4ABC")
    named: list[tuple[str, Frame]] = [
        ("enrollment", enrollment_screen(token, "v0.1.0", measurer)),
        ("status-booting", status_screen(BOOTING, measurer)),
        ("status-healthy", status_screen(HEALTHY, measurer)),
        ("menu-first", menu_screen(Menu(), measurer)),
        ("menu-reboot", menu_screen(Menu(cursor=3), measurer)),
        ("network", network_screen(HEALTHY, measurer)),
    ]
    named.extend(
        (f"error-{error.code}", error_screen(error, HELP_URL, measurer)) for error in CATALOGUE
    )
    return named


def contact_sheet(images: list[tuple[str, Image.Image]]) -> Image.Image:
    """Grille agrandie avec le nom de chaque ecran au-dessus."""
    cell_w, cell_h = WIDTH * SCALE, HEIGHT * SCALE + LABEL_HEIGHT
    rows = -(-len(images) // COLUMNS)
    sheet = Image.new(
        "L",
        (COLUMNS * cell_w + (COLUMNS + 1) * GUTTER, rows * cell_h + (rows + 1) * GUTTER),
        160,
    )
    draw = ImageDraw.Draw(sheet)
    for index, (name, image) in enumerate(images):
        col, row = index % COLUMNS, index // COLUMNS
        x = GUTTER + col * (cell_w + GUTTER)
        y = GUTTER + row * (cell_h + GUTTER)
        draw.text((x, y), name, fill=0, font=font(13))
        scaled = image.resize((cell_w, HEIGHT * SCALE), Image.Resampling.NEAREST)
        sheet.paste(scaled.convert("L"), (x, y + LABEL_HEIGHT))
    return sheet


def main(out_dir: Path) -> None:
    """Ecrit un PNG par ecran et `contact-sheet.png`."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[tuple[str, Image.Image]] = []
    for name, frame in screens():
        image = render(frame)
        image.save(out_dir / f"{name}.png")
        rendered.append((name, image))
    sheet_path = out_dir / "contact-sheet.png"
    contact_sheet(rendered).save(sheet_path)
    print(f"{len(rendered)} ecrans -> {out_dir}")
    print(f"planche contact -> {sheet_path}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("out/screens"))
