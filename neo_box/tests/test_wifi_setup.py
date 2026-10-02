"""Le scénario d'installation WiFi, piloté par des adaptateurs factices."""

from neo_box.features.wifi_setup.application.wifi_setup import WifiSetup
from neo_box.features.wifi_setup.domain.wifi import WifiCredentials


class FakeAp:
    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True


class FakePortal:
    def __init__(self, credentials: WifiCredentials | None) -> None:
        self._credentials = credentials
        self.calls = 0

    def collect(self) -> WifiCredentials | None:
        self.calls += 1
        return self._credentials


class FakeJoiner:
    def __init__(self, *, success: bool = True) -> None:
        self._success = success
        self.joined: list[WifiCredentials] = []

    def join(self, credentials: WifiCredentials) -> bool:
        self.joined.append(credentials)
        return self._success


class FakeInternet:
    def __init__(self, online_after: int = 0) -> None:
        self._online_after = online_after
        self.checks = 0

    def online(self) -> bool:
        self.checks += 1
        return self.checks > self._online_after


class FakeClock:
    def __init__(self) -> None:
        self.slept = 0.0

    def sleep(self, seconds: float) -> None:
        self.slept += seconds


def _setup(
    **kwargs: object,
) -> tuple[WifiSetup, FakeAp, FakePortal, FakeJoiner, FakeInternet, FakeClock]:
    ap = FakeAp()
    portal = FakePortal(kwargs.get("credentials", WifiCredentials("Maison", "secret")))
    joiner = FakeJoiner(success=kwargs.get("join_success", True))
    internet = FakeInternet(kwargs.get("online_after", 1))
    clock = FakeClock()
    attempts = int(kwargs.get("attempts", 4))
    delay = float(kwargs.get("delay", 1.0))
    setup = WifiSetup(ap, portal, joiner, internet, clock, attempts=attempts, delay=delay)
    return setup, ap, portal, joiner, internet, clock


def test_deja_en_ligne_n_ouvre_pas_l_ap() -> None:
    setup, ap, portal, joiner, _, _ = _setup(online_after=0)
    assert setup.run() is True
    assert ap.started is False
    assert portal.calls == 0
    assert joiner.joined == []


def test_ouvre_l_ap_rejoint_et_confirme_internet() -> None:
    setup, ap, portal, joiner, internet, _ = _setup(online_after=2)
    assert setup.run() is True
    assert ap.started is True
    assert ap.stopped is True
    assert portal.calls == 1
    assert joiner.joined == [WifiCredentials("Maison", "secret")]
    # 1er check initial (hors ligne), puis 2 vérifs après le join avant d'être en ligne.
    assert internet.checks == 3


def test_abandon_sans_identifiants_ferme_l_ap() -> None:
    setup, ap, _, joiner, _, _ = _setup(credentials=None)
    assert setup.run() is False
    assert ap.stopped is True
    assert joiner.joined == []


def test_echec_du_join_ferme_l_ap() -> None:
    setup, ap, _, joiner, _, _ = _setup(join_success=False)
    assert setup.run() is False
    assert ap.stopped is True
    assert joiner.joined == [WifiCredentials("Maison", "secret")]


def test_internet_jamais_la_apres_le_join() -> None:
    setup, ap, _, joiner, _, clock = _setup(online_after=99)
    assert setup.run() is False
    assert ap.stopped is True
    assert joiner.joined == [WifiCredentials("Maison", "secret")]
    assert clock.slept == 4.0  # 4 tentatives x 1.0 s
