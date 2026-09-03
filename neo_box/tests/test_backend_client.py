from neo_box.features.app.infra.backend import BackendClient, BackendReporter, BackendSupport
from neo_box.features.status.domain.state import BoxState, HaHealth, Link
from tests.conftest import LocalServer

STATE = BoxState(
    internet=Link.UP,
    home_assistant=HaHealth.RUNNING,
    zigbee_coordinator=Link.UP,
    zigbee_devices=4,
    ip_address="10.0.0.2",
    hostname="neo-box",
    version="v0.1.0",
)


def test_announce_envoie_le_jeton_et_rend_la_reponse(local_server: LocalServer) -> None:
    local_server.respond("POST", "/api/boxes/announce", 200, {"status": "unclaimed"})
    client = BackendClient(local_server.url + "/", lambda: None)
    assert client.announce("7K3M9PQR2STVWXYZ4ABC", "serial", "v1") == {"status": "unclaimed"}
    sent = local_server.received[-1]
    assert sent.body == {
        "provisioning_token": "7K3M9PQR2STVWXYZ4ABC",
        "hardware_id": "serial",
        "version": "v1",
    }
    assert "Authorization" not in sent.headers


def test_heartbeat_porte_la_cle_et_la_telemetrie(local_server: LocalServer) -> None:
    local_server.respond("POST", "/api/boxes/me/heartbeat", 200, {"status": "ok"})
    BackendReporter(
        BackendClient(local_server.url, lambda: "neo_box_k"), lambda: "neo_box_k"
    ).report(STATE, "E20")
    sent = local_server.received[-1]
    assert sent.headers["Authorization"] == "Bearer neo_box_k"
    assert sent.body["error_code"] == "E20"
    assert sent.body["version"] == "v0.1.0"
    assert sent.body["state"]["zigbee_devices"] == 4
    assert sent.body["state"]["home_assistant"] == "running"
    assert sent.body["state"]["ip_address"] == "10.0.0.2"


def test_sans_cle_le_reporter_ne_tente_rien(local_server: LocalServer) -> None:
    BackendReporter(BackendClient(local_server.url, lambda: None), lambda: None).report(STATE, None)
    assert local_server.received == []


def test_un_heartbeat_refuse_ne_leve_pas(local_server: LocalServer) -> None:
    local_server.respond("POST", "/api/boxes/me/heartbeat", 401)
    BackendReporter(BackendClient(local_server.url, lambda: "k" * 56), lambda: "k").report(
        STATE, None
    )


def test_demande_d_assistance(local_server: LocalServer) -> None:
    local_server.respond(
        "POST", "/api/boxes/me/support-requests", 201, {"id": "s1", "status": "open"}
    )
    BackendSupport(BackendClient(local_server.url, lambda: "neo_box_k")).request_session()
    sent = local_server.received[-1]
    assert sent.path == "/api/boxes/me/support-requests"
    assert sent.headers["Authorization"] == "Bearer neo_box_k"


def test_assistance_hors_ligne_ne_leve_pas() -> None:
    BackendSupport(BackendClient("http://127.0.0.1:1", lambda: "k")).request_session()
