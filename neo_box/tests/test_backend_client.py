from neo_box.features.app.infra.backend import (
    BackendClient,
    BackendHaTokenRegistrar,
    BackendReporter,
    BackendSupport,
)
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


def test_demande_de_code_d_appairage(local_server: LocalServer) -> None:
    local_server.respond(
        "POST", "/api/boxes/me/pairing-code", 201, {"pairingCode": "ABCDEFGHJKMN"}
    )
    client = BackendClient(local_server.url, lambda: "neo_box_k")
    assert client.pairing_code() == {"pairingCode": "ABCDEFGHJKMN"}
    sent = local_server.received[-1]
    assert sent.path == "/api/boxes/me/pairing-code"
    assert sent.headers["Authorization"] == "Bearer neo_box_k"


def test_tire_la_configuration_desiree(local_server: LocalServer) -> None:
    local_server.respond("GET", "/api/boxes/me/config", 200, {"config": {"theme": "neo"}})
    client = BackendClient(local_server.url, lambda: "neo_box_k")
    assert client.get_config() == {"config": {"theme": "neo"}}
    sent = local_server.received[-1]
    assert sent.method == "GET"
    assert sent.headers["Authorization"] == "Bearer neo_box_k"


def test_accuse_reception_de_la_configuration(local_server: LocalServer) -> None:
    local_server.respond("POST", "/api/boxes/me/config/applied", 200, {"status": "ok"})
    client = BackendClient(local_server.url, lambda: "neo_box_k")
    client.report_applied_config({"theme": "neo"})
    sent = local_server.received[-1]
    assert sent.path == "/api/boxes/me/config/applied"
    assert sent.body == {"theme": "neo"}
    assert sent.headers["Authorization"] == "Bearer neo_box_k"


def test_enregistre_le_jeton_ha(local_server: LocalServer) -> None:
    local_server.respond("POST", "/api/boxes/me/ha-token", 200, {"status": "ok"})
    client = BackendClient(local_server.url, lambda: "neo_box_k")
    client.register_ha_token("ha-token-123")
    sent = local_server.received[-1]
    assert sent.path == "/api/boxes/me/ha-token"
    assert sent.body == {"token": "ha-token-123"}
    assert sent.headers["Authorization"] == "Bearer neo_box_k"


def test_registrar_enregistre_une_seule_fois(local_server: LocalServer) -> None:
    local_server.respond("POST", "/api/boxes/me/ha-token", 200, {"status": "ok"})
    registrar = BackendHaTokenRegistrar(
        BackendClient(local_server.url, lambda: "k"), lambda: True, lambda: "ha-token"
    )
    registrar.register_if_enrolled()
    registrar.register_if_enrolled()
    assert len(local_server.received) == 1


def test_registrar_silencieux_avant_enrolement(local_server: LocalServer) -> None:
    registrar = BackendHaTokenRegistrar(
        BackendClient(local_server.url, lambda: "k"), lambda: False, lambda: "ha-token"
    )
    registrar.register_if_enrolled()
    assert local_server.received == []


def test_signale_un_snapshot(local_server: LocalServer) -> None:
    local_server.respond("POST", "/api/boxes/me/snapshots", 201, {"status": "ok"})
    client = BackendClient(local_server.url, lambda: "neo_box_k")
    client.report_snapshot("abc123")
    sent = local_server.received[-1]
    assert sent.path == "/api/boxes/me/snapshots"
    assert sent.body == {"slug": "abc123"}
    assert sent.headers["Authorization"] == "Bearer neo_box_k"
