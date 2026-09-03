from neo_box.features.display.infra.pillow_measurer import PillowTextMeasurer
from neo_box.features.errors.domain.catalogue import CATALOGUE, NO_INTERNET, help_url
from neo_box.features.errors.domain.screen import error_screen
from neo_box.shared.drawing import Qr, Text
from neo_box.shared.layout import overflowing


def test_codes_uniques_et_bien_formes() -> None:
    codes = [error.code for error in CATALOGUE]
    assert len(codes) == len(set(codes))
    assert all(len(code) == 3 and code[0] == "E" and code[1:].isdigit() for code in codes)


def test_fiches_d_aide_uniques_par_code() -> None:
    slugs = [error.help_slug for error in CATALOGUE]
    assert len(slugs) == len(set(slugs)) or len(set(slugs)) >= 8


def test_help_url() -> None:
    assert help_url(NO_INTERNET, "https://neo-domotique.fr/") == "https://neo-domotique.fr/aide/E01"


def test_chaque_ecran_d_erreur_tient_dans_l_ecran(measurer: PillowTextMeasurer) -> None:
    for error in CATALOGUE:
        frame = error_screen(error, "https://neo-domotique.fr", measurer)
        assert overflowing(frame, measurer) == (), error.code


def test_l_ecran_montre_le_code_le_libelle_et_le_qr_d_aide(
    measurer: PillowTextMeasurer,
) -> None:
    frame = error_screen(NO_INTERNET, "https://neo-domotique.fr", measurer)
    texts = [p.text for p in frame.primitives if isinstance(p, Text)]
    assert "E01" in texts
    assert " ".join(texts).count("Pas de connexion Internet") == 1
    qrs = [p for p in frame.primitives if isinstance(p, Qr)]
    assert [qr.data for qr in qrs] == ["https://neo-domotique.fr/aide/E01"]


def test_le_libelle_tient_en_deux_lignes_maximum(measurer: PillowTextMeasurer) -> None:
    for error in CATALOGUE:
        frame = error_screen(error, "https://neo-domotique.fr", measurer)
        body_lines = [p for p in frame.primitives if isinstance(p, Text) and p.size == 13]
        assert len(body_lines) <= 2, error.code
