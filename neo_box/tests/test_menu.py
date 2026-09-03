from neo_box.features.display.infra.pillow_measurer import PillowTextMeasurer
from neo_box.features.menu.domain.menu import MAIN_ITEMS, Menu, MenuAction
from neo_box.features.menu.domain.screen import menu_screen
from neo_box.shared.drawing import Box, Text
from neo_box.shared.keys import Key
from neo_box.shared.layout import overflowing


def test_le_menu_principal_couvre_les_gestes_de_l_installateur() -> None:
    actions = [item.action for item in MAIN_ITEMS]
    assert actions == [
        MenuAction.PERMIT_JOIN,
        MenuAction.SUPPORT_SESSION,
        MenuAction.SHOW_NETWORK,
        MenuAction.REBOOT,
        MenuAction.BACK,
    ]


def test_bas_et_haut_bouclent() -> None:
    menu = Menu()
    assert menu.move(Key.DOWN).cursor == 1
    assert menu.move(Key.UP).cursor == len(MAIN_ITEMS) - 1
    assert Menu(cursor=len(MAIN_ITEMS) - 1).move(Key.DOWN).cursor == 0


def test_les_autres_touches_ne_bougent_pas_le_curseur() -> None:
    menu = Menu(cursor=2)
    for key in (Key.LEFT, Key.RIGHT, Key.OK, Key.BACK):
        assert menu.move(key) == menu


def test_l_ecran_tient_pour_chaque_position(measurer: PillowTextMeasurer) -> None:
    for cursor in range(len(MAIN_ITEMS)):
        frame = menu_screen(Menu(cursor=cursor), measurer)
        assert overflowing(frame, measurer) == (), cursor


def test_l_entree_courante_est_en_video_inverse(measurer: PillowTextMeasurer) -> None:
    frame = menu_screen(Menu(cursor=1), measurer)
    inverted = [p.text for p in frame.primitives if isinstance(p, Text) and p.inverted]
    assert MAIN_ITEMS[1].label in inverted
    assert MAIN_ITEMS[0].label not in inverted
    # une bande pleine derriere l'entree courante, en plus du bandeau de titre
    assert len([p for p in frame.primitives if isinstance(p, Box) and p.filled]) == 2
