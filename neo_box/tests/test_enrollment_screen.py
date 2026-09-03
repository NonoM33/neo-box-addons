from neo_box.features.display.infra.pillow_measurer import PillowTextMeasurer
from neo_box.features.display.infra.pillow_renderer import qr_module_pixels
from neo_box.features.enrollment.domain.screen import QR_SIZE, enrollment_screen
from neo_box.features.enrollment.domain.token import ProvisioningToken
from neo_box.shared.drawing import Qr, Text
from neo_box.shared.layout import overflowing

TOKEN = ProvisioningToken("7K3M9PQR2STVWXYZ4ABC")
MIN_MODULE_PIXELS = 3


def test_tient_dans_l_ecran(measurer: PillowTextMeasurer) -> None:
    frame = enrollment_screen(TOKEN, "v0.1.0", measurer)
    assert overflowing(frame, measurer) == ()


def test_le_qr_contient_le_jeton_avec_son_schema(measurer: PillowTextMeasurer) -> None:
    frame = enrollment_screen(TOKEN, "v0.1.0", measurer)
    qrs = [p for p in frame.primitives if isinstance(p, Qr)]
    assert [qr.data for qr in qrs] == ["NEO:7K3M9PQR2STVWXYZ4ABC"]


def test_le_qr_reste_scannable_sur_un_ecran_de_250_px() -> None:
    # En dessous de 3 px par module (~0,6 mm sur un 2,13"), un telephone ne lit plus le code.
    assert qr_module_pixels(TOKEN.qr_payload, QR_SIZE) >= MIN_MODULE_PIXELS


def test_le_code_complet_est_lisible_en_clair(measurer: PillowTextMeasurer) -> None:
    frame = enrollment_screen(TOKEN, "v0.1.0", measurer)
    small = "".join(
        p.text for p in frame.primitives if isinstance(p, Text) and p.size == 11 and not p.inverted
    )
    assert small.replace("-", "") == TOKEN.value


def test_la_version_est_dans_le_bandeau(measurer: PillowTextMeasurer) -> None:
    frame = enrollment_screen(TOKEN, "v0.1.0", measurer)
    assert any(isinstance(p, Text) and p.text == "v0.1.0" for p in frame.primitives)
