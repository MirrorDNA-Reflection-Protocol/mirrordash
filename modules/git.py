"""Git module — recent activity, branch, status."""
import os
from pathlib import Path
from rich.panel import Panel
from rich.text import Text
from rich import box
from .core import clr, _run


def render(profile):
    color = clr(profile.get("color"))

    # Use CWD or first git repo found
    cwd = Path(os.getcwd())
    branch = _run(f"git -C '{cwd}' rev-parse --abbrev-ref HEAD 2>/dev/null") or "—"
    status = _run(f"git -C '{cwd}' status --short 2>/dev/null")
    log = _run(f"git -C '{cwd}' log --oneline -5 --format='%h %s' 2>/dev/null")

    changed = len([l for l in status.splitlines() if l.strip()]) if status else 0

    t = Text()
    t.append(f"  branch  ", style="grey50")
    t.append(f"{branch}\n", style=f"bold {color}")

    if changed:
        t.append(f"  {changed} changed file(s)\n", style="yellow")
    else:
        t.append("  working tree clean\n", style="green")

    if log:
        t.append("\n")
        for line in log.splitlines()[:5]:
            parts = line.split(" ", 1)
            if len(parts) == 2:
                t.append(f"  {parts[0]} ", style="grey42")
                t.append(f"{parts[1]}\n", style="grey85")

    return Panel(t, title=f"[{color}]GIT[/{color}]",
                 border_style="grey30", box=box.SIMPLE_HEAD, padding=(0, 1))
