"""Où la box mémorise la dernière configuration appliquée."""

import json
from pathlib import Path
from typing import Any


class FileConfigStore:
    """Un fichier JSON dans /data : la dernière config appliquée."""

    def __init__(self, path: Path) -> None:
        """Garde le chemin."""
        self._path = path

    def last_applied(self) -> dict[str, Any] | None:
        """La config du fichier, ou None si absent/illisible."""
        try:
            data = json.loads(self._path.read_text())
        except (OSError, ValueError):
            return None
        return data if isinstance(data, dict) else None

    def save(self, config: dict[str, Any]) -> None:
        """Écrit la config (répertoire créé au besoin)."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(config))
