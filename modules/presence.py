"""Presence module — team member status."""
import json
from datetime import datetime, timezone
from rich.panel import Panel
from rich.text import Text
from rich import box
from .core import clr, PRESENCE_FILE


def render(profile):
    color = clr(profile.get("color"))

    if not PRESENCE_FILE.exists():
        t = Text()
        t.append("  No team presence data.\n", style="grey50")
        t.append("  Write JSON to ~/.mirrordash/presence.json\n\n", style="grey30")
        t.append('  [{"name": "alice", "status": "flow", "task": "..."}]\n', style="grey23")
        return Panel(t, title=f"[{color}]PRESENCE[/{color}]",
                     border_style=color, box=box.HEAVY_HEAD, padding=(0, 1))

    try:
        members = json.loads(PRESENCE_FILE.read_text())
    except Exception:
        members = []

    STATUS_COLORS = {
        "flow": "green", "deep": "cyan", "blocked": "yellow",
        "offline": "grey23", "active": "bright_white",
    }

    t = Text()
    for m in members[:8]:
        status = m.get("status", "offline").lower()
        sc = STATUS_COLORS.get(status, "white")
        dot = "●" if status != "offline" else "○"
        t.append(f"  [{sc}]{dot}[/{sc}] ")
        t.append(f"{m.get('name','?'):<12}", style="white" if status != "offline" else "grey30")
        t.append(f"{m.get('task', '')[:35]}", style="grey70" if status != "offline" else "grey23")
        t.append(f"  [{sc}]{status.upper()}[/{sc}]\n")

    online = sum(1 for m in members if m.get("status", "offline") != "offline")
    t.append(f"\n  {online}/{len(members)} online\n", style="grey50")

    return Panel(t, title=f"[{color}]PRESENCE[/{color}]",
                 border_style=color, box=box.HEAVY_HEAD, padding=(0, 1))
