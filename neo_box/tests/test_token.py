import pytest

from neo_box.features.enrollment.domain.token import (
    CROCKFORD_ALPHABET,
    InvalidTokenError,
    ProvisioningToken,
)

VALID = "7K3M9PQR2STVWXYZ4ABC"


def test_un_jeton_fait_vingt_caracteres_crockford() -> None:
    assert ProvisioningToken(VALID).value == VALID


@pytest.mark.parametrize(
    "raw", ["", "7K3M", VALID + "A", "7K3M9PQR2STVWXYZ4ABU", "7K3M9PQR2STVWXYZ4AB!"]
)
def test_refuse_longueur_et_alphabet(raw: str) -> None:
    with pytest.raises(InvalidTokenError):
        ProvisioningToken(raw)


def test_parse_normalise_la_saisie_humaine() -> None:
    # minuscules, tirets, espaces, et glyphes confondables corriges (o->0, i/l->1)
    assert ProvisioningToken.parse(" 7k3m-9pqr-2stv-wxyz-4abc ").value == VALID
    assert ProvisioningToken.parse("Ok3M9PQR2STVWXYZ4ABC").value == "0K3M9PQR2STVWXYZ4ABC"
    assert ProvisioningToken.parse("iK3M9PQR2STVWXYZ4ABl").value == "1K3M9PQR2STVWXYZ4AB1"


def test_parse_accepte_le_contenu_du_qr() -> None:
    assert ProvisioningToken.parse("NEO:" + VALID).value == VALID


def test_display_groupe_par_quatre() -> None:
    assert ProvisioningToken(VALID).display == "7K3M-9PQR-2STV-WXYZ-4ABC"


def test_qr_payload_porte_le_schema() -> None:
    assert ProvisioningToken(VALID).qr_payload == "NEO:" + VALID


def test_generate_donne_des_jetons_valides_et_distincts() -> None:
    tokens = {ProvisioningToken.generate().value for _ in range(50)}
    assert len(tokens) == 50
    assert all(c in CROCKFORD_ALPHABET for token in tokens for c in token)
