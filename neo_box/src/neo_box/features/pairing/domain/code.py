"""Le code d'appairage client : 12 caracteres Crockford affiches par la box (QR `NEO:APPAIRER:…`).

Le code est GENERE par le backend (`POST /api/boxes/me/pairing-code`) : la box le recoit,
l'affiche, et le client le scanne pour autoriser son telephone. La box ne le devine jamais.
"""

from dataclasses import dataclass

CROCKFORD_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
CODE_LENGTH = 12
GROUP_SIZE = 4
QR_SCHEME = "NEO:APPAIRER:"
_CORRECTIONS = str.maketrans({"O": "0", "I": "1", "L": "1"})


class InvalidPairingCodeError(ValueError):
    """Le texte fourni n'est pas un code d'appairage."""


@dataclass(frozen=True, slots=True)
class PairingCode:
    """Code normalise : 12 caracteres Crockford, sans separateur."""

    value: str

    def __post_init__(self) -> None:
        """Refuse tout ce qui n'est pas exactement un code bien forme."""
        if len(self.value) != CODE_LENGTH or any(c not in CROCKFORD_ALPHABET for c in self.value):
            msg = f"code d'appairage invalide : {self.value!r}"
            raise InvalidPairingCodeError(msg)

    @classmethod
    def parse(cls, raw: str) -> "PairingCode":
        """Normalise une saisie : casse, tirets, espaces, glyphes confondables."""
        cleaned = raw.strip().upper().replace("-", "").replace(" ", "")
        cleaned = cleaned.removeprefix(QR_SCHEME)
        return cls(cleaned.translate(_CORRECTIONS))

    @property
    def display(self) -> str:
        """Le code groupe par quatre, lisible et recopiable : ABCD-EFGH-JKMN."""
        groups = (self.value[i : i + GROUP_SIZE] for i in range(0, CODE_LENGTH, GROUP_SIZE))
        return "-".join(groups)

    @property
    def qr_payload(self) -> str:
        """Ce que contient le QR : un schema court, pas une URL."""
        return QR_SCHEME + self.value
