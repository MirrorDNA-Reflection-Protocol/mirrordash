"""Memory Map — CONTINUITY, CC_MEMORY, bus state, handoffs, freshness."""
import json
import time
from pathlib import Path
from datetime import datetime
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Group
from rich import box
from .core import clr

HOME = Path.home()
MIRRORDNA = HOME / ".mirrordna"

MEMORY_FILES = {
    "CONTINUITY.md":     MIRRORDNA / "CONTINUITY.md",
    "CC_MEMORY.md":      MIRRORDNA / "CC_MEMORY.md",
    "SHIPLOG.md":        MIRRORDNA / "SHIPLOG.md",
    "FACTS.md":          MIRRORDNA / "FACTS.md",
    "MISTAKES.md":       MIRRORDNA / "MISTAKES.md",
    "INFRASTRUCTURE.md": MIRRORDNA / "INFRASTRUCTURE.md",
}


def _age(path: Path) -> tuple[str, str]:
    """Return (age_str, color)."""
    if not path.exists():
        return "missing", "red"
    age_s = time.time() - path.stat().st_mtime
    if age_s < 300:
        return f"{int(age_s)}s", "green"
    if age_s < 3600:
        return f"{int(age_s/60)}m", "green"
    if age_s < 86400:
        return f"{int(age_s/3600)}h", "yellow"
    return f"{int(age_s/86400)}d", "red"


def render(profile):
    color = clr(profile.get("color", "deep_sky_blue1"))

    t = Text()
    t.append("  MEMORY FILES\n", style=f"bold {color}")

    tbl = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    tbl.add_column("file",  width=20, no_wrap=True)
    tbl.add_column("age",   width=8,  no_wrap=True)
    tbl.add_column("size",  width=8,  no_wrap=True)

    for label, path in MEMORY_FILES.items():
        age_str, age_color = _age(path)
        size = f"{path.stat().st_size // 1024}KB" if path.exists() else "—"
        tbl.add_row(
            Text(label, style="grey70"),
            Text(age_str, style=age_color),
            Text(size, style="grey42"),
        )

    # Bus state
    bus_state = MIRRORDNA / "bus/continuity/live_state.json"
    bus_txt = Text("\n  BUS STATE\n", style=f"bold {color}")
    if bus_state.exists():
        try:
            state = json.loads(bus_state.read_text())
            for k, v in list(state.items())[:6]:
                bus_txt.append(f"  {str(k):<18}", style="grey50")
                bus_txt.append(f"{str(v)[:35]}\n", style="grey70")
        except Exception:
            bus_txt.append("  (unreadable)\n", style="grey30")
    else:
        bus_txt.append("  No live state file.\n", style="grey30")

    # Handoff history
    handoff_dir = MIRRORDNA / "handoff/pending"
    handoff_txt = Text("\n  HANDOFFS\n", style=f"bold {color}")
    if handoff_dir.exists():
        pickups = sorted(handoff_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        for p in pickups[:3]:
            age_str, ac = _age(p)
            handoff_txt.append(f"  {p.name[:30]:<32}", style="grey60")
            handoff_txt.append(f"{age_str}\n", style=ac)
        if not pickups:
            handoff_txt.append("  No pending handoffs.\n", style="grey30")
    else:
        handoff_txt.append("  No handoff directory.\n", style="grey30")

    return Panel(Group(t, tbl, bus_txt, handoff_txt),
                 title=f"[{color}]MEMORY MAP[/{color}]",
                 border_style=color, box=box.HEAVY_HEAD, padding=(0, 1))
