"""Synchroniser la configuration désirée : tirer, appliquer si changée, accuser réception."""

import logging
from typing import Any, Protocol

from neo_box.features.app.infra.http import HttpError

_LOGGER = logging.getLogger(__name__)


class ConfigSource(Protocol):
    """Fournit la configuration désirée."""

    def fetch(self) -> dict[str, Any] | None:
        """La config désirée, ou None si injoignable/absente."""
        ...


class ConfigApplier(Protocol):
    """Applique la configuration localement."""

    def apply(self, config: dict[str, Any]) -> None:
        """Effet de bord local."""
        ...


class ConfigReporter(Protocol):
    """Accuse réception auprès du backend."""

    def report_applied(self, config: dict[str, Any]) -> None:
        """Signale que la config est appliquée."""
        ...


class ConfigStore(Protocol):
    """Mémorise la dernière configuration appliquée."""

    def last_applied(self) -> dict[str, Any] | None:
        """La dernière config appliquée, ou None."""
        ...

    def save(self, config: dict[str, Any]) -> None:
        """Mémorise la config appliquée."""
        ...


class BackendConfig:
    """Source + accusé de réception sur le backend (`GET/POST /api/boxes/me/config*`)."""

    def __init__(self, backend: object) -> None:
        """Garde le client backend (expose `get_config` et `report_applied_config`)."""
        self._backend = backend

    def fetch(self) -> dict[str, Any] | None:
        """La config désirée, ou None si le backend est muet."""
        try:
            reply = self._backend.get_config()  # type: ignore[attr-defined]
        except HttpError:
            _LOGGER.exception("configuration impossible à tirer")
            return None
        config = reply.get("config") if isinstance(reply, dict) else None
        return config if isinstance(config, dict) else None

    def report_applied(self, config: dict[str, Any]) -> None:
        """Accuse réception ; un échec est journalisé, jamais bloquant."""
        try:
            self._backend.report_applied_config(config)  # type: ignore[attr-defined]
        except HttpError:
            _LOGGER.exception("accusé de configuration impossible")


class NoopConfigApplier:
    """Aucune application réelle (le runtime lit encore sa config d'environnement)."""

    def apply(self, config: dict[str, Any]) -> None:
        """Rien, mais journalise ce qu'on a reçu."""
        _LOGGER.info("configuration reçue (application différée) : %d clés", len(config))


class ConfigSync:
    """Tire la config, l'applique seulement si elle a changé, puis accuse réception."""

    def __init__(
        self,
        source: ConfigSource,
        applier: ConfigApplier,
        store: ConfigStore,
        reporter: ConfigReporter,
    ) -> None:
        """Garde les quatre ports."""
        self._source = source
        self._applier = applier
        self._store = store
        self._reporter = reporter

    def sync(self) -> bool:
        """True si une nouvelle configuration a été appliquée."""
        config = self._source.fetch()
        if config is None or config == self._store.last_applied():
            return False
        self._applier.apply(config)
        self._store.save(config)
        self._reporter.report_applied(config)
        return True
