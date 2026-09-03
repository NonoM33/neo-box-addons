"""Du BoxState au code erreur affiche : une seule erreur a la fois, la plus bloquante d'abord.

L'ordre est celui de l'installateur : ce qui empeche la maison de fonctionner (HA,
antenne) passe avant ce qui empeche le support d'intervenir (Internet, cloud, mesh),
qui passe avant ce qui menace a moyen terme (disque, temperature, mise a jour).
"""

from neo_box.features.errors.domain import catalogue
from neo_box.features.errors.domain.catalogue import ErrorCode
from neo_box.features.status.domain.state import BoxState, HaHealth, Link

DISK_CRITICAL_PERCENT = 5
CPU_MAX_TEMPERATURE_C = 80.0


def diagnose(state: BoxState) -> ErrorCode | None:
    """Le code erreur a afficher, ou None si la box est saine."""
    checks: tuple[tuple[bool, ErrorCode], ...] = (
        (state.home_assistant is HaHealth.STOPPED, catalogue.HA_STOPPED),
        (state.home_assistant is HaHealth.UNRESPONSIVE, catalogue.HA_UNRESPONSIVE),
        (state.zigbee_coordinator is Link.DOWN, catalogue.ZIGBEE_COORDINATOR_MISSING),
        (state.internet is Link.DOWN, catalogue.NO_INTERNET),
        (state.cloud is Link.DOWN, catalogue.CLOUD_UNREACHABLE),
        (state.mesh is Link.DOWN, catalogue.MESH_DOWN),
        (_disk_critical(state), catalogue.DISK_FULL),
        (_overheating(state), catalogue.CPU_OVERHEAT),
        (state.last_update_failed, catalogue.UPDATE_FAILED),
    )
    for failing, error in checks:
        if failing:
            return error
    return None


def _disk_critical(state: BoxState) -> bool:
    return state.disk_free_percent is not None and state.disk_free_percent < DISK_CRITICAL_PERCENT


def _overheating(state: BoxState) -> bool:
    return state.cpu_temperature_c is not None and state.cpu_temperature_c > CPU_MAX_TEMPERATURE_C
