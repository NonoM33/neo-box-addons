"""Point d'entree de l'add-on : lit la configuration, cable les adaptateurs, boucle."""

import logging
import os
import time
from pathlib import Path

from neo_box.features.app.application.box_app import BoxApp
from neo_box.features.app.application.ports import Buttons
from neo_box.features.app.application.runtime import Runtime
from neo_box.features.app.infra.controls import LiveControls, SupportUnavailable
from neo_box.features.app.infra.enrollment_store import FileEnrollmentStore
from neo_box.features.app.infra.home_assistant import HomeAssistantClient
from neo_box.features.app.infra.state_probe import LiveStateProbe
from neo_box.features.app.infra.supervisor import SupervisorClient
from neo_box.features.display.infra.pillow_measurer import PillowTextMeasurer
from neo_box.features.display.infra.png_display import PngDisplay
from neo_box.features.display.ports import Display
from neo_box.shared.keys import Key


class SystemClock:
    """Le temps reel."""

    def monotonic(self) -> float:
        """Horloge monotone du systeme."""
        return time.monotonic()

    def sleep(self, seconds: float) -> None:
        """Attente bloquante."""
        time.sleep(seconds)


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


class NoButtons:
    """Aucun bouton (developpement sans GPIO)."""

    def poll(self) -> Key | None:
        """Jamais rien."""
        return None


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
    store = FileEnrollmentStore(Path(env.get("NEO_DATA_DIR", "/data")))
    version = env.get("NEO_VERSION", "dev")
    probe = LiveStateProbe(
        home_assistant=home_assistant,
        supervisor=supervisor,
        internet_check_url=env.get("NEO_INTERNET_CHECK_URL", "https://neo-domotique.fr/"),
        cloud_health_url=env.get("NEO_BACKEND_URL") or None,
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
        enrollment=store,
        controls=LiveControls(home_assistant, supervisor, SupportUnavailable()),
        clock=SystemClock(),
        measurer=PillowTextMeasurer(),
    )
    runtime.run()


if __name__ == "__main__":
    main()
