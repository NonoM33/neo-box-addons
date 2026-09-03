from dataclasses import replace

from neo_box.features.display.infra.pillow_measurer import PillowTextMeasurer
from neo_box.features.errors.domain import catalogue
from neo_box.features.status.domain.diagnosis import diagnose
from neo_box.features.status.domain.screen import network_screen, status_screen
from neo_box.features.status.domain.state import BoxState, HaHealth, Link
from neo_box.shared.drawing import Text
from neo_box.shared.layout import overflowing

HEALTHY = BoxState(
    internet=Link.UP,
    cloud=Link.UP,
    mesh=Link.UP,
    home_assistant=HaHealth.RUNNING,
    zigbee_coordinator=Link.UP,
    zigbee_devices=3,
    ip_address="192.168.1.42",
    hostname="neo-box",
    version="v0.1.0",
    disk_free_percent=50,
    cpu_temperature_c=45.0,
)
WORST = replace(
    HEALTHY,
    internet=Link.DOWN,
    cloud=Link.DOWN,
    home_assistant=HaHealth.UNRESPONSIVE,
    zigbee_coordinator=Link.DOWN,
    ip_address="192.168.100.200",
    hostname="neo-box-nom-interminable-qui-deborde-forcement",
    version="v10.20.30",
)


def test_box_saine_aucune_erreur() -> None:
    assert diagnose(HEALTHY) is None


def test_etat_inconnu_n_est_pas_une_erreur() -> None:
    assert diagnose(BoxState()) is None


def test_ordre_de_priorite_des_erreurs() -> None:
    # tout casse en meme temps : HA d'abord, puis l'antenne, puis le reseau
    everything = replace(
        WORST, home_assistant=HaHealth.STOPPED, disk_free_percent=1, cpu_temperature_c=95.0
    )
    assert diagnose(everything) == catalogue.HA_STOPPED
    assert diagnose(replace(everything, home_assistant=HaHealth.RUNNING)) == (
        catalogue.ZIGBEE_COORDINATOR_MISSING
    )
    no_ha_no_zigbee = replace(
        everything, home_assistant=HaHealth.RUNNING, zigbee_coordinator=Link.UP
    )
    assert diagnose(no_ha_no_zigbee) == catalogue.NO_INTERNET
    assert diagnose(replace(no_ha_no_zigbee, internet=Link.UP)) == catalogue.CLOUD_UNREACHABLE


def test_ha_qui_ne_repond_pas_a_son_propre_code() -> None:
    assert diagnose(replace(HEALTHY, home_assistant=HaHealth.UNRESPONSIVE)) == (
        catalogue.HA_UNRESPONSIVE
    )


def test_seuils_disque_et_temperature() -> None:
    assert diagnose(replace(HEALTHY, disk_free_percent=4)) == catalogue.DISK_FULL
    assert diagnose(replace(HEALTHY, disk_free_percent=5)) is None
    assert diagnose(replace(HEALTHY, cpu_temperature_c=80.5)) == catalogue.CPU_OVERHEAT
    assert diagnose(replace(HEALTHY, cpu_temperature_c=80.0)) is None


def test_mise_a_jour_echouee_passe_apres_tout_le_reste() -> None:
    assert diagnose(replace(HEALTHY, last_update_failed=True)) == catalogue.UPDATE_FAILED
    assert diagnose(replace(HEALTHY, last_update_failed=True, mesh=Link.DOWN)) == (
        catalogue.MESH_DOWN
    )


def test_ecran_statut_tient_dans_le_pire_cas(measurer: PillowTextMeasurer) -> None:
    for state in (HEALTHY, WORST, BoxState()):
        assert overflowing(status_screen(state, measurer), measurer) == ()


def test_ecran_statut_montre_les_quatre_liaisons_et_l_ip(measurer: PillowTextMeasurer) -> None:
    texts = [p.text for p in status_screen(HEALTHY, measurer).primitives if isinstance(p, Text)]
    for expected in (
        "Internet",
        "Cloud Neo",
        "Home Assistant",
        "Zigbee",
        "3 appareils",
        "192.168.1.42",
    ):
        assert expected in texts


def test_zigbee_singulier_et_antenne_absente(measurer: PillowTextMeasurer) -> None:
    one = replace(HEALTHY, zigbee_devices=1)
    texts = [p.text for p in status_screen(one, measurer).primitives if isinstance(p, Text)]
    assert "1 appareil" in texts
    texts = [p.text for p in status_screen(WORST, measurer).primitives if isinstance(p, Text)]
    assert "ANTENNE ABSENTE" in texts


def test_ecran_reseau_tient_et_montre_l_ip(measurer: PillowTextMeasurer) -> None:
    for state in (HEALTHY, WORST, BoxState()):
        frame = network_screen(state, measurer)
        assert overflowing(frame, measurer) == ()
    texts = [p.text for p in network_screen(HEALTHY, measurer).primitives if isinstance(p, Text)]
    assert "192.168.1.42" in texts
