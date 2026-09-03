from dataclasses import dataclass, field

import pytest

from neo_box.features.app.infra.http import HttpError
from neo_box.features.enrollment.application.enroll import EnrollmentService
from neo_box.features.enrollment.domain.token import ProvisioningToken

TOKEN = ProvisioningToken("7K3M9PQR2STVWXYZ4ABC")


@dataclass
class FakeStore:
    saved: tuple[str, str] | None = None

    def token(self) -> ProvisioningToken:
        return TOKEN

    def is_enrolled(self) -> bool:
        return self.saved is not None

    def save_credentials(self, api_key: str, box_id: str) -> None:
        self.saved = (api_key, box_id)


@dataclass
class FakeAnnouncer:
    reply: dict[str, object] = field(default_factory=dict)
    fail: bool = False
    calls: list[tuple[str, str, str]] = field(default_factory=list)

    def announce(self, token: str, hardware_id: str, version: str) -> dict[str, object]:
        self.calls.append((token, hardware_id, version))
        if self.fail:
            raise HttpError("http://backend", None, "down")
        return self.reply


def service(store: FakeStore, backend: FakeAnnouncer) -> EnrollmentService:
    return EnrollmentService(store, backend, "serial-1", "v0.1.0")


def test_tant_que_personne_n_a_rattache_la_box_elle_attend() -> None:
    store, backend = FakeStore(), FakeAnnouncer({"status": "unclaimed"})
    assert service(store, backend).is_enrolled() is False
    assert store.saved is None
    assert backend.calls == [(TOKEN.value, "serial-1", "v0.1.0")]


def test_la_cle_recue_est_gardee_et_la_box_est_enrolee() -> None:
    store = FakeStore()
    backend = FakeAnnouncer({"status": "claimed", "api_key": "neo_box_k", "box_id": "b1"})
    assert service(store, backend).is_enrolled() is True
    assert store.saved == ("neo_box_k", "b1")


def test_une_box_deja_enrolee_ne_s_annonce_plus() -> None:
    store, backend = FakeStore(saved=("k", "b")), FakeAnnouncer()
    assert service(store, backend).is_enrolled() is True
    assert backend.calls == []


def test_hors_ligne_on_reessaiera_au_prochain_tour() -> None:
    store, backend = FakeStore(), FakeAnnouncer(fail=True)
    assert service(store, backend).is_enrolled() is False


@pytest.mark.parametrize(
    "reply", [{"status": "claimed"}, {"status": "claimed", "api_key": 3, "box_id": "b"}]
)
def test_une_reponse_claimed_sans_cle_valide_n_enrole_pas(reply: dict[str, object]) -> None:
    store = FakeStore()
    assert service(store, FakeAnnouncer(reply)).is_enrolled() is False
    assert store.saved is None
