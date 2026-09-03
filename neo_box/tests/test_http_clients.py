import pytest

from neo_box.features.app.infra.home_assistant import HomeAssistantClient
from neo_box.features.app.infra.http import HttpError, request_json
from neo_box.features.app.infra.supervisor import SupervisorClient
from tests.conftest import LocalServer


def test_request_json_leve_une_erreur_typee_sur_4xx(local_server: LocalServer) -> None:
    local_server.respond("GET", "/missing", 404)
    with pytest.raises(HttpError) as excinfo:
        request_json("GET", f"{local_server.url}/missing")
    assert excinfo.value.status == 404


def test_request_json_leve_sans_statut_quand_rien_ne_repond() -> None:
    with pytest.raises(HttpError) as excinfo:
        request_json("GET", "http://127.0.0.1:1/", timeout=0.5)
    assert excinfo.value.status is None


def test_ping_home_assistant(local_server: LocalServer) -> None:
    client = HomeAssistantClient(f"{local_server.url}/core/api", "tok")
    assert client.ping() is False
    local_server.respond("GET", "/core/api/", 200, {"message": "API running."})
    assert client.ping() is True
    assert local_server.received[-1].headers["Authorization"] == "Bearer tok"


def test_permit_join_appelle_le_service_zha(local_server: LocalServer) -> None:
    local_server.respond("POST", "/core/api/services/zha/permit", 200, [])
    HomeAssistantClient(f"{local_server.url}/core/api", "tok").permit_join()
    sent = local_server.received[-1]
    assert (sent.method, sent.path) == ("POST", "/core/api/services/zha/permit")
    assert sent.body == {"duration": 120}


def test_supervisor_lit_data_et_degrade_en_vide(local_server: LocalServer) -> None:
    client = SupervisorClient(local_server.url, "sup")
    assert client.host_info() == {}
    local_server.respond("GET", "/host/info", 200, {"result": "ok", "data": {"hostname": "neo"}})
    assert client.host_info() == {"hostname": "neo"}
    assert local_server.received[-1].headers["Authorization"] == "Bearer sup"


def test_supervisor_reboot(local_server: LocalServer) -> None:
    local_server.respond("POST", "/host/reboot", 200, {"result": "ok"})
    SupervisorClient(local_server.url, "sup").reboot_host()
    assert local_server.received[-1].path == "/host/reboot"
