"""Le portail captif : une page web qui demande le WiFi de la maison."""

import html
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from neo_box.features.wifi_setup.domain.wifi import WifiCredentials


def parse_credentials(body: str) -> WifiCredentials | None:
    """Extrait ssid + password d'un corps de formulaire URL-encodé."""
    data = urllib.parse.parse_qs(body)
    ssid = (data.get("ssid") or [""])[0].strip()
    password = (data.get("password") or [""])[0]
    if not ssid:
        return None
    return WifiCredentials(ssid=ssid, password=password)


def page_html(ap_ssid: str) -> str:
    """La page du portail, prête à servir."""
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Neo — connexion de la box</title>
  <style>
    body {{ font-family: -apple-system, system-ui, sans-serif; background: #0f1420;
           color: #e6e9ef; display: flex; min-height: 100vh; margin: 0;
           align-items: center; justify-content: center; }}
    main {{ background: #1a2130; padding: 32px; border-radius: 16px;
            width: min(92vw, 400px); box-shadow: 0 10px 40px #0006; }}
    h1 {{ font-size: 20px; margin: 0 0 4px; }}
    p {{ color: #9aa3b2; font-size: 14px; margin: 0 0 20px; }}
    label {{ display: block; font-size: 13px; color: #c7cdd8; margin: 12px 0 4px; }}
    input {{ width: 100%; box-sizing: border-box; background: #0f1420; border: 1px solid #2c3648;
            color: #e6e9ef; border-radius: 8px; padding: 10px 12px; font-size: 15px; }}
    button {{ width: 100%; margin-top: 20px; background: #d99020; color: #141414;
              border: 0; border-radius: 8px; padding: 12px; font-size: 15px; font-weight: 600; }}
  </style>
</head>
<body>
<main>
  <h1>Connexion de la box Neo</h1>
  <p>Vous êtes connecté au point d'accès <strong>{html.escape(ap_ssid)}</strong>.
     Entrez le WiFi de la maison pour mettre la box en ligne.</p>
  <form method="post" action="/connect">
    <label for="ssid">Nom du réseau (SSID)</label>
    <input id="ssid" name="ssid" required autofocus>
    <label for="password">Mot de passe WiFi</label>
    <input id="password" name="password" type="password" required>
    <button type="submit">Connecter la box</button>
  </form>
</main>
</body>
</html>"""


class HttpPortal:
    """Un serveur HTTP minimal : GET sert le formulaire, POST /connect le recueille."""

    def __init__(
        self, host: str = "0.0.0.0", port: int = 8080, ap_ssid: str = "NeoBox-Setup"  # noqa: S104
    ) -> None:
        """Garde l'adresse, le port et le nom du point d'accès."""
        self._host = host
        self._port = port
        self._ap_ssid = ap_ssid
        self._credentials: WifiCredentials | None = None
        self._received = threading.Event()
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Ouvre le serveur dans un thread de fond."""
        portal = self

        class Handler(BaseHTTPRequestHandler):
            """Sert le formulaire et recueille la soumission."""

            def do_GET(self) -> None:
                self._html(200, page_html(portal._ap_ssid))

            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length).decode("utf-8")
                credentials = parse_credentials(body)
                if credentials is not None:
                    portal._credentials = credentials
                    portal._received.set()
                self._html(200, "<p>Connexion en cours… vous pouvez fermer cette page.</p>")

            def _html(self, status: int, body: str) -> None:
                self.send_response(status)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(body.encode("utf-8"))

            def log_message(self, *args: object) -> None:
                """Silence les journaux par requête."""

        self._server = ThreadingHTTPServer((self._host, self._port), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def collect(self) -> WifiCredentials | None:
        """Bloque jusqu'à la soumission du formulaire."""
        self._received.wait()
        return self._credentials

    def stop(self) -> None:
        """Arrête le serveur s'il tourne."""
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
