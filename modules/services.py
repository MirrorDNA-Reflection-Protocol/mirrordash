"""Services module — port/process health check."""
import socket
from pathlib import Path
from rich.panel import Panel
from rich.text import Text
from rich import box
from .core import clr, DASH_DIR, _run

SERVICES_FILE = DASH_DIR / "services.yaml"

_DEFAULTS = [
    {"name": "localhost:8080", "port": 8080},
]


def _load_services():
    if not SERVICES_FILE.exists():
        return _DEFAULTS
    try:
        import yaml
        return yaml.safe_load(SERVICES_FILE.read_text()) or _DEFAULTS
    except Exception:
        return _DEFAULTS


def _check(port):
    try:
        with socket.create_connection(("localhost", port), timeout=0.5):
            return True
    except Exception:
        return False


def render(profile):
    color = clr(profile.get("color"))
    services = _load_services()

    t = Text()
    up = 0
    for svc in services[:12]:
        name = svc.get("name", str(svc.get("port", "?")))
        port = svc.get("port")
        ok = _check(port) if port else False
        if ok:
            up += 1
        dot = "[green]●[/]" if ok else "[red]●[/]"
        t.append("  ")
        t.append_text(Text.from_markup(dot))
        label_color = "grey85" if ok else "grey42"
        t.append(f" {name}", style=label_color)
        if port:
            t.append(f" :{port}", style="grey30")
        t.append("\n")

    total = len(services)
    t.append(f"\n  {up}/{total} up", style="green" if up == total else "yellow")

    if not SERVICES_FILE.exists():
        t.append("  — configure ~/.mirrordash/services.yaml\n", style="grey30")

    return Panel(t, title=f"[{color}]SERVICES[/{color}]",
                 border_style=color, box=box.HEAVY_HEAD, padding=(0, 1))
