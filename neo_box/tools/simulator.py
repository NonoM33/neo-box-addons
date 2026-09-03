"""Simulateur de box : le vrai daemon, un ecran PNG et une face avant cliquable dans le navigateur.

    NEO_BACKEND_URL=http://localhost:3000 uv run python tools/simulator.py
    -> http://localhost:8765

Tout est reel sauf le materiel : machine a etats, ecrans, enrolement contre le backend,
heartbeat. Les sondes sont remplacees par des interrupteurs dans la page.
"""

import json
import logging
import os
import sys
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass, replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from neo_box.__main__ import SystemClock, _cloud
from neo_box.features.app.application.box_app import BoxApp
from neo_box.features.app.application.runtime import Runtime
from neo_box.features.app.infra.enrollment_store import FileEnrollmentStore
from neo_box.features.display.infra.pillow_measurer import PillowTextMeasurer
from neo_box.features.display.infra.png_display import PngDisplay
from neo_box.features.mesh.infra.tailscale import NoMeshAgent
from neo_box.features.status.domain.diagnosis import diagnose
from neo_box.features.status.domain.state import BoxState, HaHealth, Link
from neo_box.shared.keys import Key

PORT = int(os.environ.get("NEO_SIM_PORT", "8765"))
OUT = Path(os.environ.get("NEO_SIM_DIR", "out/sim"))
VERSION = "v0.1.0-sim"
PAGE = Path(__file__).with_name("simulator.html")


@dataclass
class SimButtons:
    """Touches injectees par la page."""

    queue: deque[Key]

    def poll(self) -> Key | None:
        """La plus ancienne pression."""
        return self.queue.popleft() if self.queue else None


class SimProbe:
    """Sondes pilotees par les interrupteurs de la page."""

    def __init__(self) -> None:
        """Demarre saine."""
        self.state = BoxState(
            internet=Link.UP,
            cloud=Link.UP,
            mesh=Link.UP,
            home_assistant=HaHealth.RUNNING,
            zigbee_coordinator=Link.UP,
            zigbee_devices=7,
            ip_address="192.168.1.42",
            hostname="neo-box-sim",
            version=VERSION,
            disk_free_percent=61,
            cpu_temperature_c=47.0,
        )

    def read(self) -> BoxState:
        """L'etat courant."""
        return self.state

    def apply(self, patch: dict[str, Any]) -> None:
        """Modifie l'etat depuis un JSON de la page."""
        fields: dict[str, Any] = {}
        for name, value in patch.items():
            if name in ("internet", "cloud", "mesh", "zigbee_coordinator"):
                fields[name] = Link(value)
            elif name == "home_assistant":
                fields[name] = HaHealth(value)
            elif name in ("zigbee_devices", "disk_free_percent"):
                fields[name] = int(value)
            elif name == "cpu_temperature_c":
                fields[name] = float(value)
            elif name in ("ip_address", "hostname"):
                fields[name] = value or None
            elif name == "last_update_failed":
                fields[name] = bool(value)
        self.state = replace(self.state, **fields)


class Simulator:
    """Le daemon dans un thread, et ce que la page a besoin de voir."""

    def __init__(self) -> None:
        """Cable le runtime avec les fakes materiel et le vrai backend s'il est configure."""
        self.buttons = SimButtons(deque())
        self.probe = SimProbe()
        self.store = FileEnrollmentStore(OUT / "data")
        self.backend_url = os.environ.get("NEO_BACKEND_URL") or None
        enrollment, support, reporter, _ = _cloud(
            self.backend_url, self.store, NoMeshAgent(), VERSION
        )
        from neo_box.features.app.infra.controls import LiveControls  # noqa: PLC0415
        from neo_box.features.app.infra.home_assistant import HomeAssistantClient  # noqa: PLC0415
        from neo_box.features.app.infra.supervisor import SupervisorClient  # noqa: PLC0415

        ha = HomeAssistantClient("http://127.0.0.1:1", "sim")
        supervisor = SupervisorClient("http://127.0.0.1:1", "sim")
        self.app = BoxApp(
            help_base_url="https://neo-domotique.fr",
            token=None if self.store.is_enrolled() else self.store.token(),
        )
        self.runtime = Runtime(
            app=self.app,
            display=PngDisplay(OUT / "screens"),
            buttons=self.buttons,
            probe=self.probe,
            enrollment=enrollment,
            controls=LiveControls(ha, supervisor, support),
            reporter=reporter,
            clock=SystemClock(),
            measurer=PillowTextMeasurer(),
            refresh_seconds=5.0,
        )
        self.actions: deque[str] = deque(maxlen=20)
        threading.Thread(target=self.runtime.run, daemon=True).start()

    def info(self) -> dict[str, Any]:
        """Ce que la page affiche a cote de l'ecran."""
        error = diagnose(self.probe.state)
        api_key = self.store.api_key()
        return {
            "token": self.store.token().display,
            "qr": self.store.token().qr_payload,
            "enrolled": api_key is not None,
            "api_key_prefix": api_key[:12] + "..." if api_key else None,
            "mode": self.app.mode.name,
            "error": error.code if error else None,
            "backend": self.backend_url,
            "state": {k: getattr(v, "value", v) for k, v in asdict(self.probe.state).items()},
            "actions": list(self.actions),
        }

    def reset(self) -> None:
        """Oublie l'enrolement : la box redevient neuve (nouveau jeton)."""
        for path in (self.store.credentials_path, self.store.token_path):
            path.unlink(missing_ok=True)
        self.app.token = self.store.token()
        self.app.mode = type(self.app.mode).ENROLLING


class Handler(BaseHTTPRequestHandler):
    """Routes de la page."""

    sim: Simulator

    def do_GET(self) -> None:
        """Page, image de l'ecran, ou infos JSON."""
        if self.path.startswith("/screen.png"):
            latest = OUT / "screens" / "latest.png"
            self._bytes(latest.read_bytes() if latest.exists() else b"", "image/png")
        elif self.path.startswith("/info"):
            self._json(self.sim.info())
        else:
            self._bytes(PAGE.read_bytes(), "text/html; charset=utf-8")

    def do_POST(self) -> None:
        """Touche, etat des sondes, ou remise a neuf."""
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length)) if length else {}
        if self.path.startswith("/key/"):
            self.sim.buttons.queue.append(Key[self.path.rsplit("/", 1)[1]])
        elif self.path == "/state":
            self.sim.probe.apply(body)
            self.sim.runtime._last_refresh = None  # noqa: SLF001 - simulateur : force le rafraichissement
        elif self.path == "/reset":
            self.sim.reset()
        time.sleep(0.15)
        self._json(self.sim.info())

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: ANN401
        """Silence."""
        del fmt, args

    def _json(self, payload: dict[str, Any]) -> None:
        self._bytes(json.dumps(payload).encode(), "application/json")

    def _bytes(self, data: bytes, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> None:
    """Lance le daemon et le serveur de la page."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    Handler.sim = Simulator()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"simulateur -> http://localhost:{PORT}  (backend: {Handler.sim.backend_url or 'aucun'})")
    server.serve_forever()


if __name__ == "__main__":
    main()
