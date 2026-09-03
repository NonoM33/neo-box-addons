"""Les actions du menu, cablees sur les vrais services."""

import logging
from dataclasses import dataclass
from typing import Protocol

from neo_box.features.app.infra.home_assistant import HomeAssistantClient
from neo_box.features.app.infra.supervisor import SupervisorClient

_LOGGER = logging.getLogger(__name__)


class SupportPort(Protocol):
    """Demande d'assistance a distance (portee par le backend Neo)."""

    def request_session(self) -> None:
        """Demande l'ouverture d'une session."""
        ...


class SupportUnavailable:
    """Tant que l'enrolement backend n'est pas cable, la demande est seulement journalisee."""

    def request_session(self) -> None:
        """Trace la demande pour qu'elle ne soit pas perdue en silence."""
        _LOGGER.warning("assistance a distance demandee, mais aucun backend configure")


@dataclass(frozen=True)
class LiveControls:
    """Implemente `Controls` avec HA (ZHA), le Supervisor et le port support."""

    home_assistant: HomeAssistantClient
    supervisor: SupervisorClient
    support: SupportPort

    def permit_join(self) -> None:
        """Ouvre ZHA a l'appairage."""
        self.home_assistant.permit_join()

    def request_support_session(self) -> None:
        """Delegue au port support."""
        self.support.request_session()

    def reboot(self) -> None:
        """Redemarre l'hote via le Supervisor."""
        self.supervisor.reboot_host()
