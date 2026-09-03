"""Point d'entree de l'add-on : lit la configuration, cable les adaptateurs, boucle."""

import logging
import os
import time
from pathlib import Path

from neo_box.features.app.application.box_app import BoxApp
from neo_box.features.app.application.ports import Buttons, EnrollmentStatus, Reporter
from neo_box.features.app.application.runtime import Runtime
from neo_box.features.app.infra.backend import BackendClient, BackendReporter, BackendSupport
from neo_box.features.app.infra.controls import LiveControls, SupportPort, SupportUnavailable
from neo_box.features.app.infra.enrollment_store import FileEnrollmentStore
from neo_box.features.app.infra.hardware import hardware_id
from neo_box.features.app.infra.home_assistant import HomeAssistantClient
from neo_box.features.app.infra.state_probe import LiveStateProbe
from neo_box.features.app.infra.supervisor import SupervisorClient
from neo_box.features.display.infra.pillow_measurer import PillowTextMeasurer
from neo_box.features.display.infra.png_display import PngDisplay
from neo_box.features.display.ports import Display
from neo_box.features.enrollment.application.enroll import EnrollmentService
from neo_box.features.mesh.infra.tailscale import NoMeshAgent, TailscaleAgent
from neo_box.features.mesh.ports import MeshAgent
from neo_box.features.status.domain.state import BoxState
from neo_box.shared.keys import Key


class SystemClock:
    """Le temps reel."""

    def monotonic(self) -> float:
        """Horloge monotone du systeme."""
        return time.monotonic()

    def sleep(self, seconds: float) -> None:
        """Attente bloquante."""
        time.sleep(seconds)


class NoButtons:
    """Aucun bouton (developpement sans GPIO)."""

    def poll(self) -> Key | None:
        """Jamais rien."""
        return None


class NoReporter:
    """Aucun backend configure : la telemetrie reste locale."""

    def report(self, state: BoxState, error_code: str | None) -> None:
        """Rien."""


def _display(kind: str, png_dir: Path) -> Display:
    if kind == "waveshare":
        from neo_box.features.display.infra.waveshare_display import (  # noqa: PLC0415
            WaveshareDisplay,
        )

        return WaveshareDisplay.open()
    return PngDisplay(png_dir)


def _buttons(spec: str) -> Buttons:
    from neo_box.features.app.infra.gpio_buttons import GpioButtons  # noqa: PLC0415

    pins = {Key[name]: int(pin) for name, pin in (item.split("=") for item in spec.split(","))}
    return GpioButtons(pins)


def _mesh_agent(kind: str, data_dir: Path) -> MeshAgent:
    return TailscaleAgent(data_dir / "mesh") if kind == "tailscale" else NoMeshAgent()


def _cloud(
    backend_url: str | None, store: FileEnrollmentStore, mesh: MeshAgent, version: str
) -> tuple[EnrollmentStatus, SupportPort, Reporter, str | None]:
    """Sans backend, la box vit seule : enrolement local, pas d'assistance, pas de heartbeat."""
    if not backend_url:
        return store, SupportUnavailable(), NoReporter(), None
    backend = BackendClient(backend_url, store.api_key)
    serial = hardware_id(os.environ.get("NEO_HARDWARE_ID", "unknown"))
    return (
        EnrollmentService(store, backend, mesh, serial, version),
        BackendSupport(backend),
        BackendReporter(backend, store.api_key),
        f"{backend_url.rstrip('/')}/health",
    )


def main() -> None:
    """Assemble et lance la boucle."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    env = os.environ
    supervisor_token = env.get("SUPERVISOR_TOKEN", "")
    supervisor = SupervisorClient(
        env.get("NEO_SUPERVISOR_URL", "http://supervisor"), supervisor_token
    )
    home_assistant = HomeAssistantClient(
        env.get("NEO_HA_URL", "http://supervisor/core/api"), supervisor_token
    )
    data_dir = Path(env.get("NEO_DATA_DIR", "/data"))
    store = FileEnrollmentStore(data_dir)
    version = env.get("NEO_VERSION", "dev")
    mesh = _mesh_agent(env.get("NEO_MESH", "none"), data_dir)
    enrollment, support, reporter, cloud_health_url = _cloud(
        env.get("NEO_BACKEND_URL") or None, store, mesh, version
    )
    probe = LiveStateProbe(
        home_assistant=home_assistant,
        supervisor=supervisor,
        mesh=mesh,
        internet_check_url=env.get("NEO_INTERNET_CHECK_URL", "https://neo-domotique.fr/"),
        cloud_health_url=cloud_health_url,
        zigbee_device_glob=env.get("NEO_ZIGBEE_DEVICE_GLOB", "/dev/serial/by-id/*"),
        version=version,
    )
    app = BoxApp(
        help_base_url=env.get("NEO_HELP_URL", "https://neo-domotique.fr"),
        token=None if store.is_enrolled() else store.token(),
    )
    buttons_spec = env.get("NEO_BUTTON_PINS", "")
    runtime = Runtime(
        app=app,
        display=_display(
            env.get("NEO_DISPLAY", "png"), Path(env.get("NEO_PNG_DIR", "/data/screens"))
        ),
        buttons=_buttons(buttons_spec) if buttons_spec else NoButtons(),
        probe=probe,
        enrollment=enrollment,
        controls=LiveControls(home_assistant, supervisor, support),
        reporter=reporter,
        clock=SystemClock(),
        measurer=PillowTextMeasurer(),
    )
    runtime.run()


if __name__ == "__main__":
    main()
