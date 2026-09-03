from neo_box.shared.drawing import Box, Frame, HLine, Qr, Text
from neo_box.shared.layout import (
    HEIGHT,
    WIDTH,
    bounds,
    ellipsize,
    overflowing,
    right_aligned,
    wrap,
)
from tests.conftest import FixedMeasurer


def test_wrap_coupe_sur_les_espaces_sans_depasser(fixed: FixedMeasurer) -> None:
    # size 10 -> 5 px par caractere ; 40 px = 8 caracteres
    assert wrap("un deux trois quatre", 40, 10, fixed) == ("un deux", "trois", "quatre")


def test_wrap_garde_un_mot_trop_long_sur_sa_propre_ligne(fixed: FixedMeasurer) -> None:
    assert wrap("ok interminablement ok", 40, 10, fixed) == ("ok", "interminablement", "ok")


def test_wrap_texte_vide(fixed: FixedMeasurer) -> None:
    assert wrap("", 40, 10, fixed) == ()


def test_ellipsize_laisse_intact_ce_qui_tient(fixed: FixedMeasurer) -> None:
    assert ellipsize("court", 100, 10, fixed) == "court"


def test_ellipsize_raccourcit_avec_trois_points(fixed: FixedMeasurer) -> None:
    result = ellipsize("beaucoup trop long pour la place", 50, 10, fixed)
    assert result.endswith("...")
    assert fixed.measure(result, 10)[0] <= 50


def test_bounds_de_chaque_primitive(fixed: FixedMeasurer) -> None:
    assert bounds(Text(1, 2, "abcd", 10), fixed).w == 20
    assert bounds(Qr(0, 0, "x", 30), fixed).h == 30
    assert bounds(Box(5, 5, 10, 20), fixed).bottom == 25
    assert bounds(HLine(0, 7, 50), fixed).right == 50


def test_overflowing_detecte_ce_qui_sort(fixed: FixedMeasurer) -> None:
    inside = Text(0, 0, "ok", 10)
    too_right = Text(WIDTH - 5, 0, "abcdef", 10)
    too_low = Box(0, HEIGHT - 2, 10, 10)
    frame = Frame((inside, too_right, too_low))
    assert overflowing(frame, fixed) == (too_right, too_low)


def test_right_aligned_cale_le_bord_droit(fixed: FixedMeasurer) -> None:
    text = right_aligned("abcd", 100, 3, 10, fixed)
    assert bounds(text, fixed).right == 100
