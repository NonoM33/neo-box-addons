from pathlib import Path

from neo_box.features.display.infra.pillow_renderer import qr_matrix, qr_module_pixels, render
from neo_box.features.display.infra.png_display import PngDisplay
from neo_box.shared.drawing import Box, Frame, HLine, Qr, Text
from neo_box.shared.layout import HEIGHT, WIDTH


def test_l_image_fait_la_taille_de_l_ecran_en_un_bit() -> None:
    image = render(Frame(()))
    assert image.size == (WIDTH, HEIGHT)
    assert image.mode == "1"
    assert image.getpixel((0, 0)) == 255


def test_un_rectangle_plein_est_noir_et_un_texte_inverse_est_blanc_dessus() -> None:
    frame = Frame((Box(0, 0, 100, 20, filled=True), Text(2, 2, "OK", 13, inverted=True)))
    image = render(frame)
    assert image.getpixel((99, 19)) == 0
    assert image.getpixel((150, 10)) == 255
    assert image.crop((0, 0, 100, 20)).getextrema() == (0, 255)  # du blanc dans la bande noire


def test_ligne_et_contour() -> None:
    image = render(Frame((HLine(10, 50, 30), Box(100, 100, 10, 10))))
    assert image.getpixel((10, 50)) == 0
    assert image.getpixel((39, 50)) == 0
    assert image.getpixel((40, 50)) == 255
    assert image.getpixel((100, 100)) == 0
    assert image.getpixel((105, 105)) == 255


def test_le_qr_est_trace_a_l_echelle_entiere_et_centre() -> None:
    data = "NEO:7K3M9PQR2STVWXYZ4ABC"
    modules = len(qr_matrix(data))
    scale = qr_module_pixels(data, 98)
    assert scale * modules <= 98
    image = render(Frame((Qr(4, 20, data, 98),)))
    offset = (98 - scale * modules) // 2
    # premier module du motif de reperage (apres la zone de silence d'un module)
    x = 4 + offset + scale + scale // 2
    y = 20 + offset + scale + scale // 2
    assert image.getpixel((x, y)) == 0


def test_png_display_ecrit_latest_et_un_historique(tmp_path: Path) -> None:
    display = PngDisplay(tmp_path / "screens")
    display.show(Frame((Text(0, 0, "a", 13),)))
    display.show(Frame((Text(0, 0, "b", 13),)))
    assert (tmp_path / "screens" / "latest.png").exists()
    assert sorted(p.name for p in (tmp_path / "screens").glob("0*.png")) == ["0000.png", "0001.png"]
