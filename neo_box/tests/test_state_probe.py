from pathlib import Path

from neo_box.features.app.infra.home_assistant import HomeAssistantClient
from neo_box.features.app.infra.state_probe import LiveStateProbe
from neo_box.features.app.infra.supervisor import SupervisorClient
from neo_box.features.mesh.infra.tailscale import NoMeshAgent
from neo_box.features.status.domain.state import HaHealth, Link
from tests.conftest import LocalServer


def probe(server: LocalServer, tmp_path: Path) -> LiveStateProbe:
    return LiveStateProbe(
        home_assistant=HomeAssistantClient(f"{server.url}/core/api", "t"),
        supervisor=SupervisorClient(server.url, "t"),
        mesh=NoMeshAgent(),
        internet_check_url=f"{server.url}/internet",
        cloud_health_url=f"{server.url}/health",
        zigbee_device_glob=str(tmp_path / "by-id" / "usb-*"),
        version="v0.1.0",
    )


def test_tout_injoignable_donne_down_ou_unknown(local_server: LocalServer, tmp_path: Path) -> None:
    state = probe(local_server, tmp_path).read()
    assert state.internet is Link.DOWN or state.internet is Link.UP
    assert state.home_assistant is HaHealth.UNKNOWN
    assert state.zigbee_coordinator is Link.DOWN
    assert state.ip_address is None
    assert state.version == "v0.1.0"


def test_box_saine(local_server: LocalServer, tmp_path: Path) -> None:
    (tmp_path / "by-id").mkdir()
    (tmp_path / "by-id" / "usb-Sonoff_Zigbee").touch()
    local_server.respond("GET", "/internet", 200, {})
    local_server.respond("GET", "/health", 200, {"ok": True})
    local_server.respond("GET", "/core/info", 200, {"data": {"state": "running"}})
    local_server.respond("GET", "/core/api/", 200, {})
    local_server.respond(
        "GET",
        "/host/info",
        200,
        {"data": {"hostname": "neo-box", "disk_total": 100.0, "disk_free": 42.0}},
    )
    local_server.respond(
        "GET",
        "/network/info",
        200,
        {"data": {"interfaces": [{"primary": True, "ipv4": {"address": ["192.168.1.9/24"]}}]}},
    )
    state = probe(local_server, tmp_path).read()
    assert state.internet is Link.UP
    assert state.cloud is Link.UP
    assert state.home_assistant is HaHealth.RUNNING
    assert state.zigbee_coordinator is Link.UP
    assert state.ip_address == "192.168.1.9"
    assert state.hostname == "neo-box"
    assert state.disk_free_percent == 42


def test_core_arrete_puis_ne_repondant_pas(local_server: LocalServer, tmp_path: Path) -> None:
    local_server.respond("GET", "/core/info", 200, {"data": {"state": "stopped"}})
    assert probe(local_server, tmp_path).read().home_assistant is HaHealth.STOPPED
    local_server.respond("GET", "/core/info", 200, {"data": {"state": "running"}})
    assert probe(local_server, tmp_path).read().home_assistant is HaHealth.UNRESPONSIVE


def test_un_site_qui_repond_une_erreur_http_est_quand_meme_joignable(
    local_server: LocalServer, tmp_path: Path
) -> None:
    # 404 = le reseau marche ; seule l'absence de reponse vaut coupure
    state = probe(local_server, tmp_path).read()
    assert state.internet is Link.UP
