"""Les ecrans de statut : le resume permanent et le detail reseau."""

from neo_box.features.status.domain.state import BoxState, HaHealth, Link
from neo_box.shared.drawing import Frame, Primitive, Text
from neo_box.shared.layout import (
    HEADER_HEIGHT,
    HEIGHT,
    MARGIN,
    SIZE_BODY,
    SIZE_SMALL,
    WIDTH,
    TextMeasurer,
    ellipsize,
    right_aligned,
)
from neo_box.shared.widgets import header

ROW_HEIGHT = 18
LINK_TEXT = {Link.UP: "OK", Link.DOWN: "HORS LIGNE", Link.UNKNOWN: "--"}
HA_TEXT = {
    HaHealth.RUNNING: "OK",
    HaHealth.UNRESPONSIVE: "NE REPOND PAS",
    HaHealth.STOPPED: "ARRETE",
    HaHealth.UNKNOWN: "--",
}


def status_screen(state: BoxState, measurer: TextMeasurer) -> Frame:
    """L'ecran de repos : une ligne par liaison, l'adresse IP en pied."""
    rows = (
        ("Internet", LINK_TEXT[state.internet]),
        ("Cloud Neo", LINK_TEXT[state.cloud]),
        ("Home Assistant", HA_TEXT[state.home_assistant]),
        ("Zigbee", _zigbee_text(state)),
    )
    primitives: list[Primitive] = [*header("NEO BOX", state.version, measurer)]
    y = HEADER_HEIGHT + MARGIN
    for label, value in rows:
        primitives.append(Text(MARGIN, y, label, SIZE_BODY))
        primitives.append(right_aligned(value, WIDTH - MARGIN, y, SIZE_BODY, measurer))
        y += ROW_HEIGHT
    primitives.extend(_footer(state, measurer))
    return Frame(tuple(primitives))


def network_screen(state: BoxState, measurer: TextMeasurer) -> Frame:
    """Le detail reseau, ouvert depuis le menu : IP, nom, acces distant."""
    rows = (
        ("Adresse IP", state.ip_address or "aucune"),
        ("Nom", state.hostname or "--"),
        ("Acces distant", LINK_TEXT[state.mesh]),
        ("Appareils Zigbee", str(state.zigbee_devices)),
    )
    primitives: list[Primitive] = [*header("RESEAU", "OK = retour", measurer)]
    y = HEADER_HEIGHT + MARGIN
    for label, value in rows:
        primitives.append(Text(MARGIN, y, label, SIZE_BODY))
        label_w = measurer.measure(label, SIZE_BODY)[0]
        room = WIDTH - 2 * MARGIN - label_w - MARGIN
        shown = ellipsize(value, room, SIZE_BODY, measurer)
        primitives.append(right_aligned(shown, WIDTH - MARGIN, y, SIZE_BODY, measurer))
        y += ROW_HEIGHT
    return Frame(tuple(primitives))


def _zigbee_text(state: BoxState) -> str:
    if state.zigbee_coordinator is Link.UP:
        count = state.zigbee_devices
        return f"{count} appareil" + ("s" if count > 1 else "")
    if state.zigbee_coordinator is Link.DOWN:
        return "ANTENNE ABSENTE"
    return "--"


def _footer(state: BoxState, measurer: TextMeasurer) -> tuple[Primitive, ...]:
    ip = state.ip_address or "pas d'adresse IP"
    y = HEIGHT - MARGIN - measurer.measure(ip, SIZE_SMALL)[1]
    ip_w = measurer.measure(ip, SIZE_SMALL)[0]
    room = WIDTH - 2 * MARGIN - ip_w - MARGIN
    hostname = ellipsize(state.hostname, room, SIZE_SMALL, measurer)
    return (
        Text(MARGIN, y, ip, SIZE_SMALL),
        right_aligned(hostname, WIDTH - MARGIN, y, SIZE_SMALL, measurer),
    )
