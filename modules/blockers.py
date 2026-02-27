"""Blockers module — items preventing progress. Blinks red if any active."""
from pathlib import Path
from rich.panel import Panel
from rich.text import Text
from rich import box
from .core import clr, DASH_DIR

BLOCKERS_FILE = DASH_DIR / "blockers.md"


def _read_blockers():
    if not BLOCKERS_FILE.exists():
        return []
    lines = BLOCKERS_FILE.read_text().splitlines()
    return [l.strip().lstrip("- ").strip() for l in lines
            if l.strip() and not l.strip().startswith("#")]


def render(profile):
    color = clr(profile.get("color"))
    blockers = _read_blockers()

    t = Text()
    if blockers:
        t.append(f"  {len(blockers)} BLOCKER(S)\n\n", style="bold red")
        for item in blockers[:8]:
            t.append("  ✗ ", style="red")
            t.append(f"{item}\n", style="bold white")
    else:
        t.append("  ✓ No blockers\n", style="bold green")
        t.append("  Add to ~/.mirrordash/blockers.md\n", style="grey30")

    frame = profile.get("_frame", 0)
    if blockers:
        border = "bright_red" if frame % 2 == 0 else "red"
    else:
        border = "green"

    return Panel(t, title=f"[{color}]BLOCKERS[/{color}]",
                 border_style=border, box=box.HEAVY_HEAD, padding=(0, 1))
