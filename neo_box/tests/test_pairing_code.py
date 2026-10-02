import pytest

from neo_box.features.pairing.domain.code import InvalidPairingCodeError, PairingCode


def test_parse_normalise_et_corrige_les_glyphes() -> None:
    assert PairingCode.parse("NEO:APPAIRER:ABCD-EFGH-JKMN").value == "ABCDEFGHJKMN"
    assert PairingCode.parse("oil0-1abc-defg").value == "01101ABCDEFG"


def test_display_groupe_par_quatre() -> None:
    assert PairingCode("ABCDEFGHJKMN").display == "ABCD-EFGH-JKMN"


def test_qr_payload_porte_le_schema() -> None:
    assert PairingCode("ABCDEFGHJKMN").qr_payload == "NEO:APPAIRER:ABCDEFGHJKMN"


def test_refuse_une_longueur_incorrecte() -> None:
    with pytest.raises(InvalidPairingCodeError):
        PairingCode("ABCD")


def test_refuse_un_caractere_hors_alphabet() -> None:
    with pytest.raises(InvalidPairingCodeError):
        PairingCode("ABCDEFGHJKML")  # L n'existe pas en Crockford
