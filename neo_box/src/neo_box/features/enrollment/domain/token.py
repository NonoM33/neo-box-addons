"""Le jeton de provisioning : ce qui identifie une box neuve jusqu'a son enrolement.

Vingt caracteres en base32 Crockford (100 bits d'entropie). Crockford ne se contente
pas d'ecarter les glyphes confondables : il les CORRIGE a la lecture (O -> 0, I et
L -> 1), pour qu'un installateur qui recopie le code a la main ne soit pas rejete.
"""

from dataclasses import dataclass
from secrets import choice

CROCKFORD_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
TOKEN_LENGTH = 20
GROUP_SIZE = 4
QR_SCHEME = "NEO:"
_CORRECTIONS = str.maketrans({"O": "0", "I": "1", "L": "1"})


class InvalidTokenError(ValueError):
    """Le texte fourni n'est pas un jeton de provisioning."""


@dataclass(frozen=True, slots=True)
class ProvisioningToken:
    """Jeton normalise : 20 caracteres Crockford, sans separateur."""

    value: str

    def __post_init__(self) -> None:
        """Refuse tout ce qui n'est pas exactement un jeton bien forme."""
        if len(self.value) != TOKEN_LENGTH or any(c not in CROCKFORD_ALPHABET for c in self.value):
            msg = f"jeton invalide : {self.value!r}"
            raise InvalidTokenError(msg)

    @classmethod
    def parse(cls, raw: str) -> "ProvisioningToken":
        """Normalise une saisie humaine : casse, tirets, espaces, glyphes confondables."""
        cleaned = raw.strip().upper().replace("-", "").replace(" ", "")
        cleaned = cleaned.removeprefix(QR_SCHEME)
        return cls(cleaned.translate(_CORRECTIONS))

    @classmethod
    def generate(cls) -> "ProvisioningToken":
        """Un jeton neuf, tire avec le generateur cryptographique du systeme."""
        return cls("".join(choice(CROCKFORD_ALPHABET) for _ in range(TOKEN_LENGTH)))

    @property
    def display(self) -> str:
        """Le jeton groupe par quatre, lisible et recopiable : ABCD-EFGH-JKMN-PQRS-TVWX."""
        groups = (self.value[i : i + GROUP_SIZE] for i in range(0, TOKEN_LENGTH, GROUP_SIZE))
        return "-".join(groups)

    @property
    def qr_payload(self) -> str:
        """Ce que contient le QR : un schema court, pas une URL, pour rester scannable."""
        return QR_SCHEME + self.value
