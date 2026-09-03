"""Fixtures partagees : mesureur fixe (domaine), vraie police (integration), serveur HTTP local."""

import json
import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import pytest

from neo_box.features.display.infra.pillow_measurer import PillowTextMeasurer


class FixedMeasurer:
    """Chaque caractere fait size/2 px de large, chaque ligne size px de haut."""

    def measure(self, text: str, size: int) -> tuple[int, int]:
        return len(text) * size // 2, size


@pytest.fixture
def fixed() -> FixedMeasurer:
    return FixedMeasurer()


@pytest.fixture(scope="session")
def measurer() -> PillowTextMeasurer:
    return PillowTextMeasurer()


@dataclass
class Received:
    """Une requete vue par le serveur local."""

    method: str
    path: str
    headers: dict[str, str]
    body: Any


@dataclass
class LocalServer:
    """Serveur HTTP de test : on declare des reponses par (methode, chemin)."""

    url: str
    responses: dict[tuple[str, str], tuple[int, Any]] = field(default_factory=dict)
    received: list[Received] = field(default_factory=list)

    def respond(self, method: str, path: str, status: int, body: Any = None) -> None:
        self.responses[(method, path)] = (status, body)


@pytest.fixture
def local_server() -> Iterator[LocalServer]:
    server = LocalServer(url="")

    class Handler(BaseHTTPRequestHandler):
        def _handle(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b""
            body = json.loads(raw) if raw else None
            server.received.append(
                Received(self.command, self.path, dict(self.headers.items()), body)
            )
            status, payload = server.responses.get((self.command, self.path), (404, None))
            data = json.dumps(payload).encode() if payload is not None else b""
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        do_GET = _handle
        do_POST = _handle

        def log_message(self, fmt: str, *args: Any) -> None:
            del fmt, args

    httpd = HTTPServer(("127.0.0.1", 0), Handler)
    server.url = f"http://127.0.0.1:{httpd.server_port}"
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield server
    httpd.shutdown()
    httpd.server_close()


Factory = Callable[[], LocalServer]
