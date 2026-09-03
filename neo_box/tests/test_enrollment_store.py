import json
from pathlib import Path

from neo_box.features.app.infra.enrollment_store import FileEnrollmentStore


def test_le_jeton_est_cree_une_fois_et_relu_ensuite(tmp_path: Path) -> None:
    store = FileEnrollmentStore(tmp_path / "data")
    first = store.token()
    assert FileEnrollmentStore(tmp_path / "data").token() == first


def test_enrolee_seulement_avec_des_identifiants_lisibles(tmp_path: Path) -> None:
    store = FileEnrollmentStore(tmp_path)
    assert store.is_enrolled() is False
    store.credentials_path.write_text("pas du json")
    assert store.is_enrolled() is False
    store.credentials_path.write_text(json.dumps({"api_key": ""}))
    assert store.is_enrolled() is False
    store.credentials_path.write_text(json.dumps({"api_key": "k", "tenant_id": "t"}))
    assert store.is_enrolled() is True
