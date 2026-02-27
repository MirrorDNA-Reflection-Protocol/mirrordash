"""Focus module — current task, big and unmissable."""
from rich.panel import Panel
from rich.text import Text
from rich import box
from .core import read_tasks, clr


def render(profile):
    color = clr(profile.get("color"))
    current, queue, done = read_tasks()

    t = Text()
    if current:
        t.append("NOW\n", style=f"bold {color}")
        t.append(f"  {current}\n\n", style="bold white")
    else:
        t.append("No current task set.\n\n", style="grey50")
        t.append("  Add to ~/.mirrordash/tasks.md:\n", style="grey50")
        t.append("  > Your current task here\n", style="grey70")

    total = len(queue) + len(done)
    if total:
        pct = int(len(done) / total * 100) if total else 0
        t.append(f"  {len(done)}/{total} done  ", style="grey70")
        t.append("█" * (pct // 10), style="green")
        t.append("░" * (10 - pct // 10), style="grey23")
        t.append(f"  {pct}%\n", style="grey70")

    return Panel(t, title=f"[{color}]◇ FOCUS[/{color}]",
                 border_style=color, box=box.HEAVY_HEAD, padding=(0, 1))
