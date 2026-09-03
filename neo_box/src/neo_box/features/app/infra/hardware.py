"""L'identifiant materiel de la box : le numero de serie du Raspberry, sinon le machine-id."""

from pathlib import Path

CPUINFO = Path("/proc/cpuinfo")
MACHINE_ID = Path("/etc/machine-id")


def hardware_id(fallback: str = "unknown") -> str:
    """Numero de serie du SoC, machine-id, ou `fallback` (simulateur)."""
    try:
        for line in CPUINFO.read_text().splitlines():
            if line.startswith("Serial"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    try:
        return MACHINE_ID.read_text().strip() or fallback
    except OSError:
        return fallback
