"""L'etat observe de la box a un instant donne : une photographie, jamais une opinion."""

from dataclasses import dataclass
from enum import Enum


class Link(Enum):
    """Etat d'une liaison ou d'un composant binaire."""

    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"


class HaHealth(Enum):
    """Sante de Home Assistant, vue du Supervisor et de son API."""

    RUNNING = "running"
    UNRESPONSIVE = "unresponsive"
    STOPPED = "stopped"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class BoxState:
    """Tout ce que la box sait d'elle-meme, tel que lu par les sondes."""

    internet: Link = Link.UNKNOWN
    cloud: Link = Link.UNKNOWN
    mesh: Link = Link.UNKNOWN
    home_assistant: HaHealth = HaHealth.UNKNOWN
    zigbee_coordinator: Link = Link.UNKNOWN
    zigbee_devices: int = 0
    ip_address: str | None = None
    hostname: str = ""
    version: str = ""
    disk_free_percent: int | None = None
    cpu_temperature_c: float | None = None
    last_update_failed: bool = False
