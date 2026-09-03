"""Le catalogue des codes erreur de la box.

Un code est stable pour toujours : il figure sur les fiches d'aide, dans les tickets
support et dans la memoire des installateurs. On en ajoute, on n'en renomme jamais.
Familles : E0x reseau, E1x Home Assistant, E2x radio Zigbee, E3x systeme, E4x mises a jour.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ErrorCode:
    """Un code erreur affichable : code court, libelle en francais, fiche d'aide."""

    code: str
    label: str
    help_slug: str


NO_INTERNET = ErrorCode("E01", "Pas de connexion Internet", "internet")
CLOUD_UNREACHABLE = ErrorCode("E02", "Cloud Neo injoignable", "cloud")
MESH_DOWN = ErrorCode("E03", "Acces distant coupe", "acces-distant")
HA_STOPPED = ErrorCode("E10", "Home Assistant arrete", "home-assistant")
HA_UNRESPONSIVE = ErrorCode("E11", "Home Assistant ne repond pas", "home-assistant")
ZIGBEE_COORDINATOR_MISSING = ErrorCode("E20", "Antenne Zigbee absente", "zigbee-antenne")
ZIGBEE_NETWORK_ERROR = ErrorCode("E21", "Reseau Zigbee en erreur", "zigbee-reseau")
DISK_FULL = ErrorCode("E30", "Espace disque critique", "disque")
CPU_OVERHEAT = ErrorCode("E31", "Temperature trop elevee", "temperature")
UPDATE_FAILED = ErrorCode("E40", "Mise a jour echouee", "mise-a-jour")

CATALOGUE: tuple[ErrorCode, ...] = (
    NO_INTERNET,
    CLOUD_UNREACHABLE,
    MESH_DOWN,
    HA_STOPPED,
    HA_UNRESPONSIVE,
    ZIGBEE_COORDINATOR_MISSING,
    ZIGBEE_NETWORK_ERROR,
    DISK_FULL,
    CPU_OVERHEAT,
    UPDATE_FAILED,
)


def help_url(error: ErrorCode, base_url: str) -> str:
    """L'adresse de la fiche d'aide, encodee dans le QR de l'ecran d'erreur."""
    return f"{base_url.rstrip('/')}/aide/{error.code}"
