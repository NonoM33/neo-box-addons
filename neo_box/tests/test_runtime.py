from collections import deque
from dataclasses import dataclass, field

from neo_box.features.app.application.box_app import BoxApp
from neo_box.features.app.application.runtime import Runtime
from neo_box.features.enrollment.domain.token import ProvisioningToken
from neo_box.features.status.domain.state import BoxState, Link
from neo_box.shared.drawing import Frame
from neo_box.shared.keys import Key
from tests.conftest import FixedMeasurer


@dataclass
class FakeDisplay:
    shown: list[Frame] = field(default_factory=list)

    def show(self, frame: Frame) -> None:
        self.shown.append(frame)

    def sleep(self) -> None:
        pass


@dataclass
class FakeButtons:
    presses: deque[Key] = field(default_factory=deque)

    def poll(self) -> Key | None:
        return self.presses.popleft() if self.presses else None


@dataclass
class FakeProbe:
    state: BoxState = field(default_factory=BoxState)
    reads: int = 0

    def read(self) -> BoxState:
        self.reads += 1
        return self.state


@dataclass
class FakeEnrollment:
    enrolled: bool = False

    def is_enrolled(self) -> bool:
        return self.enrolled


@dataclass
class FakeControls:
    calls: list[str] = field(default_factory=list)

    def permit_join(self) -> None:
        self.calls.append("permit_join")

    def request_support_session(self) -> None:
        self.calls.append("support")

    def reboot(self) -> None:
        self.calls.append("reboot")


@dataclass
class FakeReporter:
    reports: list[tuple[BoxState, str | None]] = field(default_factory=list)

    def report(self, state: BoxState, error_code: str | None) -> None:
        self.reports.append((state, error_code))


@dataclass
class FakeClock:
    now: float = 0.0

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


@dataclass
class Harness:
    display: FakeDisplay
    buttons: FakeButtons
    probe: FakeProbe
    enrollment: FakeEnrollment
    controls: FakeControls
    reporter: FakeReporter
    clock: FakeClock
    runtime: Runtime


def harness(fixed: FakeButtons | None = None, token: ProvisioningToken | None = None) -> Harness:
    display, buttons = FakeDisplay(), fixed or FakeButtons()
    probe, enrollment, controls, clock = FakeProbe(), FakeEnrollment(), FakeControls(), FakeClock()
    reporter = FakeReporter()
    runtime = Runtime(
        app=BoxApp(help_base_url="https://aide", token=token),
        display=display,
        buttons=buttons,
        probe=probe,
        enrollment=enrollment,
        controls=controls,
        reporter=reporter,
        clock=clock,
        measurer=FixedMeasurer(),
        refresh_seconds=30,
    )
    return Harness(display, buttons, probe, enrollment, controls, reporter, clock, runtime)


def test_le_premier_pas_lit_les_sondes_et_affiche() -> None:
    h = harness()
    h.runtime.step()
    assert h.probe.reads == 1
    assert len(h.display.shown) == 1


def test_sans_changement_l_ecran_n_est_pas_rafraichi() -> None:
    h = harness()
    for _ in range(5):
        h.runtime.step()
    assert len(h.display.shown) == 1


def test_les_sondes_ne_sont_relues_qu_a_l_intervalle() -> None:
    h = harness()
    h.runtime.step()
    h.clock.now = 29
    h.runtime.step()
    assert h.probe.reads == 1
    h.clock.now = 30
    h.runtime.step()
    assert h.probe.reads == 2


def test_une_touche_change_l_ecran_et_une_commande_est_executee() -> None:
    h = harness()
    h.runtime.step()
    h.buttons.presses.extend([Key.OK, Key.OK])
    h.runtime.step()
    h.runtime.step()
    assert h.controls.calls == ["permit_join"]
    assert len(h.display.shown) == 3  # statut, menu, retour statut


def test_un_changement_d_etat_rafraichit_l_ecran() -> None:
    h = harness()
    h.runtime.step()
    h.probe.state = BoxState(internet=Link.DOWN)
    h.clock.now = 30
    h.runtime.step()
    assert len(h.display.shown) == 2


def test_l_enrolement_est_detecte_au_rafraichissement() -> None:
    h = harness(token=ProvisioningToken("7K3M9PQR2STVWXYZ4ABC"))
    h.runtime.step()
    h.enrollment.enrolled = True
    h.clock.now = 30
    h.runtime.step()
    assert h.runtime.app.token is None
    assert len(h.display.shown) == 2


def test_chaque_rafraichissement_remonte_l_etat_et_le_code_erreur() -> None:
    h = harness()
    h.runtime.step()
    assert h.reporter.reports == [(BoxState(), None)]
    h.probe.state = BoxState(internet=Link.DOWN)
    h.clock.now = 30
    h.runtime.step()
    assert h.reporter.reports[-1] == (BoxState(internet=Link.DOWN), "E01")
