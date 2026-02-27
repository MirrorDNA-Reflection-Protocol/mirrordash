"""Loops module — open items / blockers."""
from rich.panel import Panel
from rich.text import Text
from rich import box
from .core import read_loops, clr


def render(profile):
    color = clr(profile.get("color"))
    loops = read_loops()

    t = Text()
    if loops:
        for item in loops[:10]:
            t.append("  ○ ", style="yellow")
            t.append(f"{item}\n", style="grey85")
    else:
        t.append("  No open loops.\n", style="grey50")
        t.append("  Add to ~/.mirrordash/loops.md\n", style="grey30")

    return Panel(t, title=f"[yellow]LOOPS ({len(loops)})[/yellow]",
                 border_style="grey30", box=box.SIMPLE_HEAD, padding=(0, 1))
