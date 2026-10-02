"""Détection d'Internet par simple requête HTTP."""

import urllib.error
import urllib.request

_MAX_OK_STATUS = 500


class UrlInternetChecker:
    """Considère la box en ligne si une URL répond en moins de `timeout`."""

    def __init__(self, url: str, timeout: float = 5.0) -> None:
        """Garde l'URL de contrôle et le délai."""
        self._url = url
        self._timeout = timeout

    def online(self) -> bool:
        """True si l'URL répond (tout statut < 500 compte)."""
        try:
            with urllib.request.urlopen(self._url, timeout=self._timeout) as response:  # noqa: S310
                return bool(response.status < _MAX_OK_STATUS)
        except (urllib.error.URLError, OSError):
            return False
