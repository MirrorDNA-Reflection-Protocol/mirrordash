"""Decisions module — recent decisions log."""
from pathlib import Path
from rich.panel import Panel
from rich.text import Text
from rich import box
from .core import clr, DASH_DIR

DECISIONS_FILE = DASH_DIR / "decisions.md"


def _read_decisions():
    if not DECISIONS_FILE.exists():
        return []
    lines = DECISIONS_FILE.read_text().splitlines()
    items = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        # Format: "YYYY-MM-DD: Decision text" or "- Decision text"
        items.append(s.lstrip("- ").strip())
    return items


def render(profile):
    color = clr(profile.get("color"))
    decisions = _read_decisions()

    t = Text()
    if decisions:
        t.append(f"  {len(decisions)} decision(s) logged\n\n", style="grey50")
        for item in decisions[-8:]:
            # Split date prefix if present
            if ": " in item and len(item) > 12 and item[:10].count("-") == 2:
                date, rest = item.split(": ", 1)
                t.append(f"  {date}  ", style="grey42")
                t.append(f"{rest}\n", style="grey85")
            else:
                t.append("  · ", style=f"{color}")
                t.append(f"{item}\n", style="grey85")
    else:
        t.append("  No decisions logged.\n", style="grey50")
        t.append("  Add to ~/.mirrordash/decisions.md\n", style="grey30")
        t.append("  Format: YYYY-MM-DD: Decision text\n", style="grey23")

    return Panel(t, title=f"[{color}]DECISIONS[/{color}]",
                 border_style=color, box=box.HEAVY_HEAD, padding=(0, 1))
