from typing import Any

from neo_box.features.config.application.config_sync import ConfigSync


class FakeSource:
    def __init__(self, config: dict[str, Any] | None) -> None:
        self.config = config
        self.calls = 0

    def fetch(self) -> dict[str, Any] | None:
        self.calls += 1
        return self.config


class FakeApplier:
    def __init__(self) -> None:
        self.applied: list[dict[str, Any]] = []

    def apply(self, config: dict[str, Any]) -> None:
        self.applied.append(config)


class FakeStore:
    def __init__(self, last: dict[str, Any] | None = None) -> None:
        self.last = last
        self.saved: dict[str, Any] | None = None

    def last_applied(self) -> dict[str, Any] | None:
        return self.last

    def save(self, config: dict[str, Any]) -> None:
        self.saved = config
        self.last = config


class FakeReporter:
    def __init__(self) -> None:
        self.reported: list[dict[str, Any]] = []

    def report_applied(self, config: dict[str, Any]) -> None:
        self.reported.append(config)


def test_applique_et_accuse_une_configuration_nouvelle() -> None:
    source = FakeSource({"theme": "neo"})
    applier = FakeApplier()
    store = FakeStore()
    reporter = FakeReporter()
    assert ConfigSync(source, applier, store, reporter).sync() is True
    assert applier.applied == [{"theme": "neo"}]
    assert reporter.reported == [{"theme": "neo"}]
    assert store.saved == {"theme": "neo"}


def test_n_applique_pas_une_configuration_deja_vue() -> None:
    applier = FakeApplier()
    reporter = FakeReporter()
    sync = ConfigSync(
        FakeSource({"theme": "neo"}), applier, FakeStore(last={"theme": "neo"}), reporter
    )
    assert sync.sync() is False
    assert applier.applied == []
    assert reporter.reported == []


def test_ne_fait_rien_sans_configuration() -> None:
    applier = FakeApplier()
    reporter = FakeReporter()
    assert ConfigSync(FakeSource(None), applier, FakeStore(), reporter).sync() is False
    assert applier.applied == []
    assert reporter.reported == []
