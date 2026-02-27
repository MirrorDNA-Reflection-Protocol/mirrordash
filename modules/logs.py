"""Logs module — recent alerts + system log tail."""
import json
import time
from pathlib import Path
from rich.panel import Panel
from rich.text import Text
from rich import box
from .core import clr

ALERTS_FILE  = Path.home() / ".mirrordna/health/proactive_alerts.json"
HEALTH_LOG   = Path.home() / ".mirrordna/health/health.log"
BUS_DIR      = Path.home() / ".mirrordna/bus"


def _load_alerts():
    if not ALERTS_FILE.exists():
        return []
    try:
        data = json.loads(ALERTS_FILE.read_text())
        if isinstance(data, list):
            return data[-10:]
        return []
    except Exception:
        return []


def _tail_log(path, n=8):
    if not path.exists():
        return []
    try:
        lines = path.read_text().splitlines()
        return [l for l in lines if l.strip()][-n:]
    except Exception:
        return []


def render(profile):
    color = clr(profile.get("color"))
    alerts = _load_alerts()
    log_lines = _tail_log(HEALTH_LOG)

    t = Text()
    now = time.time()

    # Alerts section
    if alerts:
        critical = [a for a in alerts if a.get("level", "").lower() in ("critical", "error")]
        warn = [a for a in alerts if a.get("level", "").lower() == "warning"]
        t.append(f"  ALERTS  ", style=f"bold {color}")
        if critical:
            t.append(f"{len(critical)} critical  ", style="bold red")
        if warn:
            t.append(f"{len(warn)} warnings\n\n", style="bold yellow")
        if not critical and not warn:
            t.append("all clear\n\n", style="bold green")

        for alert in reversed(alerts[-6:]):
            level = alert.get("level", "info").lower()
            msg = alert.get("message", alert.get("msg", str(alert)))[:60]
            lc = "red" if level in ("critical", "error") else "yellow" if level == "warning" else "grey50"
            t.append(f"  {'!' if lc != 'grey50' else '·'} ", style=lc)
            t.append(f"{msg}\n", style="grey80" if lc != "grey50" else "grey50")
    else:
        t.append("  ALERTS  ", style=f"bold {color}")
        t.append("none\n\n", style="bold green")

    # Log tail
    if log_lines:
        t.append("  LOG TAIL\n", style=f"bold {color}")
        for line in log_lines[-5:]:
            # Color ERROR/WARN lines
            if "ERROR" in line or "CRITICAL" in line:
                t.append(f"  {line[:70]}\n", style="red")
            elif "WARN" in line:
                t.append(f"  {line[:70]}\n", style="yellow")
            else:
                t.append(f"  {line[:70]}\n", style="grey42")
    else:
        t.append("  No log file at ~/.mirrordna/health/health.log\n", style="grey30")

    # Blink if critical alerts
    frame = profile.get("_frame", 0)
    critical_alerts = [a for a in alerts if a.get("level", "").lower() in ("critical", "error")]
    if critical_alerts:
        border = "bright_red" if frame % 2 == 0 else "red"
    elif alerts and any(a.get("level", "").lower() == "warning" for a in alerts):
        border = "yellow" if frame % 2 == 0 else "dark_orange"
    else:
        border = color

    return Panel(t, title=f"[{color}]LOGS[/{color}]",
                 border_style=border, box=box.HEAVY_HEAD, padding=(0, 1))
