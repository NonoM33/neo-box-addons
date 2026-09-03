"""Les sondes reelles : ce que la box observe d'elle-meme a chaque rafraichissement."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from neo_box.features.app.infra.home_assistant import HomeAssistantClient
from neo_box.features.app.infra.http import HttpError, request_json
from neo_box.features.app.infra.supervisor import SupervisorClient
from neo_box.features.mesh.ports import MeshAgent
from neo_box.features.status.domain.state import BoxState, HaHealth, Link


@dataclass(frozen=True)
class LiveStateProbe:
    """Compose les sondes HTTP et systeme en un BoxState."""

    home_assistant: HomeAssistantClient
    supervisor: SupervisorClient
    mesh: MeshAgent
    internet_check_url: str
    cloud_health_url: str | None
    zigbee_device_glob: str
    version: str

    def read(self) -> BoxState:
        """Une photographie complete ; chaque sonde degrade en UNKNOWN plutot que de lever."""
        host = self.supervisor.host_info()
        core = self.supervisor.core_info()
        return BoxState(
            internet=_reachable(self.internet_check_url),
            cloud=_reachable(self.cloud_health_url) if self.cloud_health_url else Link.UNKNOWN,
            mesh=self.mesh.status(),
            home_assistant=self._ha_health(core),
            zigbee_coordinator=_coordinator_present(self.zigbee_device_glob),
            zigbee_devices=0,
            ip_address=_primary_ipv4(self.supervisor.network_info()),
            hostname=str(host.get("hostname", "")),
            version=self.version,
            disk_free_percent=_disk_free_percent(host),
            cpu_temperature_c=_cpu_temperature(),
        )

    def _ha_health(self, core: dict[str, Any]) -> HaHealth:
        if not core:
            return HaHealth.UNKNOWN
        if core.get("state") != "running":
            return HaHealth.STOPPED
        return HaHealth.RUNNING if self.home_assistant.ping() else HaHealth.UNRESPONSIVE


def _reachable(url: str) -> Link:
    try:
        request_json("GET", url, timeout=5.0)
    except HttpError as exc:
        return Link.UP if exc.status is not None else Link.DOWN
    return Link.UP


def _coordinator_present(pattern: str) -> Link:
    root = Path(pattern).anchor or "/"
    relative = pattern.removeprefix(root)
    return Link.UP if any(Path(root).glob(relative)) else Link.DOWN


def _primary_ipv4(network: dict[str, Any]) -> str | None:
    for interface in network.get("interfaces", []):
        if not interface.get("primary"):
            continue
        addresses = interface.get("ipv4", {}).get("address", [])
        if addresses:
            return str(addresses[0]).split("/")[0]
    return None


def _disk_free_percent(host: dict[str, Any]) -> int | None:
    total, free = host.get("disk_total"), host.get("disk_free")
    if not isinstance(total, (int, float)) or not isinstance(free, (int, float)) or total <= 0:
        return None
    return round(100 * free / total)


def _cpu_temperature(path: Path = Path("/sys/class/thermal/thermal_zone0/temp")) -> float | None:
    try:
        return int(path.read_text().strip()) / 1000
    except (OSError, ValueError):
        return None
