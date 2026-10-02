from neo_box.features.display.infra.pillow_measurer import PillowTextMeasurer
from neo_box.features.display.infra.pillow_renderer import qr_module_pixels
from neo_box.features.pairing.domain.code import PairingCode
from neo_box.features.pairing.domain.screen import QR_SIZE, pairing_screen
from neo_box.shared.drawing import Qr, Text
from neo_box.shared.layout import overflowing

CODE = PairingCode("ABCDEFGHJKMN")
MIN_MODULE_PIXELS = 3


def test_tient_dans_l_ecran(measurer: PillowTextMeasurer) -> None:
    frame = pairing_screen(CODE, "v0.1.0", measurer)
    assert overflowing(frame, measurer) == ()


def test_le_qr_contient_le_code_avec_son_schema(measurer: PillowTextMeasurer) -> None:
    frame = pairing_screen(CODE, "v0.1.0", measurer)
    qrs = [p for p in frame.primitives if isinstance(p, Qr)]
    assert [qr.data for qr in qrs] == ["NEO:APPAIRER:ABCDEFGHJKMN"]


def test_le_qr_reste_scannable_sur_un_ecran_de_250_px() -> None:
    assert qr_module_pixels(CODE.qr_payload, QR_SIZE) >= MIN_MODULE_PIXELS


def test_le_code_complet_est_lisible_en_clair(measurer: PillowTextMeasurer) -> None:
    frame = pairing_screen(CODE, "v0.1.0", measurer)
    small = "".join(
        p.text for p in frame.primitives if isinstance(p, Text) and p.size == 11 and not p.inverted
    )
    assert small.replace("-", "") == CODE.value
