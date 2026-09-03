import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from neo_box.features.mesh.domain.credentials import MeshCredentials
from neo_box.features.mesh.infra.tailscale import TailscaleAgent
from neo_box.features.status.domain.state import Link

CREDS = MeshCredentials("https://mesh.example", "hskey_abc", "neo-box-1a2b")


@dataclass
class FakeRunner:
    """Bouchon de `tailscale` : rend ce qu'on lui a dit, garde les commandes."""

    returncode: int = 0
    stdout: str = ""
    stderr: str = ""
    calls: list[list[str]] = field(default_factory=list)

    def __call__(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(argv)
        return subprocess.CompletedProcess(argv, self.returncode, self.stdout, self.stderr)


def test_join_lance_tailscale_up_avec_la_cle_et_pose_le_marqueur(tmp_path: Path) -> None:
    runner = FakeRunner()
    agent = TailscaleAgent(tmp_path / "mesh", runner)
    agent.join(CREDS)
    assert runner.calls == [
        [
            "tailscale",
            "up",
            "--login-server=https://mesh.example",
            "--authkey=hskey_abc",
            "--hostname=neo-box-1a2b",
            "--accept-dns=false",
            "--accept-routes=false",
        ]
    ]
    assert agent.joined_marker.read_text() == "neo-box-1a2b"


def test_join_ne_rejoue_jamais_une_cle_a_usage_unique(tmp_path: Path) -> None:
    runner = FakeRunner()
    agent = TailscaleAgent(tmp_path, runner)
    agent.join(CREDS)
    agent.join(CREDS)
    assert len(runner.calls) == 1


def test_un_echec_ne_pose_pas_le_marqueur_pour_reessayer_plus_tard(tmp_path: Path) -> None:
    runner = FakeRunner(returncode=1, stderr="backend down")
    agent = TailscaleAgent(tmp_path, runner)
    agent.join(CREDS)
    assert not agent.joined_marker.exists()


def test_status_lit_backendstate(tmp_path: Path) -> None:
    up = FakeRunner(stdout=json.dumps({"BackendState": "Running"}))
    assert TailscaleAgent(tmp_path, up).status() is Link.UP
    stopped = FakeRunner(stdout=json.dumps({"BackendState": "NeedsLogin"}))
    assert TailscaleAgent(tmp_path, stopped).status() is Link.DOWN


def test_status_sans_daemon(tmp_path: Path) -> None:
    broken = FakeRunner(returncode=1, stderr="failed to connect")
    assert TailscaleAgent(tmp_path, broken).status() is Link.UNKNOWN
    agent = TailscaleAgent(tmp_path, broken)
    agent.joined_marker.parent.mkdir(parents=True, exist_ok=True)
    agent.joined_marker.write_text("x")
    assert agent.status() is Link.DOWN
