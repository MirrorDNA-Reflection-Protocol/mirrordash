"""Queue module — ordered task list."""
from rich.panel import Panel
from rich.text import Text
from rich import box
from .core import read_tasks, clr


def render(profile):
    color = clr(profile.get("color"))
    _, queue, done = read_tasks()

    t = Text()
    for item in done[-3:]:
        t.append(f"  ✓ {item}\n", style="grey42 strike")
    for i, item in enumerate(queue[:8]):
        marker = "▸" if i == 0 else "○"
        style = f"bold {color}" if i == 0 else "grey70"
        t.append(f"  {marker} {item}\n", style=style)

    if not queue and not done:
        t.append("  No tasks. Add to ~/.mirrordash/tasks.md\n", style="grey50")

    return Panel(t, title=f"[{color}]QUEUE[/{color}]",
                 border_style="grey30", box=box.SIMPLE_HEAD, padding=(0, 1))
