from dataclasses import replace

from neo_box.features.app.application.box_app import BoxApp, Command, Mode
from neo_box.features.enrollment.domain.token import ProvisioningToken
from neo_box.features.status.domain.state import BoxState, HaHealth, Link
from neo_box.shared.drawing import Qr, Text
from neo_box.shared.keys import Key
from tests.conftest import FixedMeasurer

TOKEN = ProvisioningToken("7K3M9PQR2STVWXYZ4ABC")
HEALTHY = BoxState(
    internet=Link.UP,
    cloud=Link.UP,
    home_assistant=HaHealth.RUNNING,
    zigbee_coordinator=Link.UP,
    version="v0.1.0",
)


def mode(app: BoxApp) -> Mode:
    return app.mode


def texts(app: BoxApp, fixed: FixedMeasurer) -> list[str]:
    return [p.text for p in app.frame(fixed).primitives if isinstance(p, Text)]


def test_une_box_neuve_affiche_le_qr_et_ignore_les_touches(fixed: FixedMeasurer) -> None:
    app = BoxApp(help_base_url="https://aide", token=TOKEN)
    assert mode(app) is Mode.ENROLLING
    for key in Key:
        assert app.on_key(key) is None
    assert mode(app) is Mode.ENROLLING
    assert any(
        isinstance(p, Qr) and p.data == TOKEN.qr_payload for p in app.frame(fixed).primitives
    )


def test_l_enrolement_bascule_sur_le_statut(fixed: FixedMeasurer) -> None:
    app = BoxApp(help_base_url="https://aide", token=TOKEN)
    app.update_state(HEALTHY)
    app.enrolled()
    assert mode(app) is Mode.HOME
    assert "NEO BOX" in texts(app, fixed)


def test_une_box_enrolee_demarre_sur_le_statut() -> None:
    assert BoxApp(help_base_url="https://aide").mode is Mode.HOME


def test_ok_ouvre_le_menu_et_retour_le_ferme(fixed: FixedMeasurer) -> None:
    app = BoxApp(help_base_url="https://aide", state=HEALTHY)
    assert app.on_key(Key.OK) is None
    assert mode(app) is Mode.MENU
    assert "MENU" in texts(app, fixed)
    assert app.on_key(Key.BACK) is None
    assert mode(app) is Mode.HOME


def test_valider_appairage_produit_la_commande_et_revient_au_statut() -> None:
    app = BoxApp(help_base_url="https://aide", state=HEALTHY)
    app.on_key(Key.OK)
    assert app.on_key(Key.OK) is Command.PERMIT_JOIN
    assert mode(app) is Mode.HOME


def test_naviguer_jusqu_au_redemarrage() -> None:
    app = BoxApp(help_base_url="https://aide", state=HEALTHY)
    app.on_key(Key.OK)
    for _ in range(3):
        assert app.on_key(Key.DOWN) is None
    assert app.on_key(Key.OK) is Command.REBOOT


def test_reseau_ouvre_l_ecran_reseau_et_toute_touche_en_sort(fixed: FixedMeasurer) -> None:
    app = BoxApp(help_base_url="https://aide", state=HEALTHY)
    app.on_key(Key.OK)
    app.on_key(Key.DOWN)
    app.on_key(Key.DOWN)
    assert app.on_key(Key.OK) is None
    assert mode(app) is Mode.NETWORK
    assert "RESEAU" in texts(app, fixed)
    app.on_key(Key.RIGHT)
    assert mode(app) is Mode.HOME


def test_retour_du_menu_par_l_entree_retour() -> None:
    app = BoxApp(help_base_url="https://aide", state=HEALTHY)
    app.on_key(Key.OK)
    app.on_key(Key.UP)  # boucle sur "Retour"
    assert app.on_key(Key.OK) is None
    assert mode(app) is Mode.HOME


def test_une_erreur_remplace_le_statut_mais_pas_le_menu(fixed: FixedMeasurer) -> None:
    app = BoxApp(help_base_url="https://aide", state=HEALTHY)
    app.update_state(replace(HEALTHY, internet=Link.DOWN))
    assert "E01" in texts(app, fixed)
    app.on_key(Key.OK)
    assert "MENU" in texts(app, fixed)
    app.on_key(Key.BACK)
    assert "E01" in texts(app, fixed)
    app.update_state(HEALTHY)
    assert "E01" not in texts(app, fixed)
