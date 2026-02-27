"""Gate Activity — live hook decisions: what was allowed, warned, blocked and why."""
import json
import time
from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from .core import clr

HOOK_DECISIONS = Path.home() / ".mirrordna/bus/hook_decisions.jsonl"

DECISION_STYLE = {
    "allow": ("·", "grey42"),
    "pass":  ("·", "grey42"),
    "warn":  ("!", "yellow"),
    "deny":  ("✗", "red"),
    "block": ("✗", "bright_red"),
}


def render(profile):
    color = clr(profile.get("color", "deep_sky_blue1"))

    if not HOOK_DECISIONS.exists():
        return Panel(Text("  No hook decisions logged yet.", style="grey50"),
                     title=f"[{color}]GATE ACTIVITY[/{color}]",
                     border_style="grey30", box=box.SIMPLE_HEAD)

    now = time.time()
    counts = {"allow": 0, "warn": 0, "block": 0, "deny": 0, "pass": 0}
    recent = []

    with open(HOOK_DECISIONS) as f:
        all_lines = f.readlines()

    for raw in all_lines:
        try:
            ev = json.loads(raw)
            d = ev.get("decision", "allow")
            if ev.get("epoch", 0) >= now - 86400:
                counts[d] = counts.get(d, 0) + 1
            if ev.get("epoch", 0) >= now - 3600:
                recent.append(ev)
        except Exception:
            pass

    recent = recent[-14:]
    total = sum(counts.values())
    blocked = counts.get("deny", 0) + counts.get("block", 0)
    warned = counts.get("warn", 0)
    allowed = counts.get("allow", 0) + counts.get("pass", 0)

    # Summary
    t = Text()
    if blocked:
        t.append(f"  ✗ {blocked} BLOCKED  ", style="bold red")
    if warned:
        t.append(f"  ! {warned} WARNED  ", style="bold yellow")
    t.append(f"  · {allowed} ok  ", style="grey60")
    t.append(f"  {total}", style="bold white")
    t.append(f" decisions / 24h\n\n", style="grey50")

    # Table of recent decisions
    tbl = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    tbl.add_column("icon", width=2, no_wrap=True)
    tbl.add_column("hook", width=20, no_wrap=True)
    tbl.add_column("decision", width=7, no_wrap=True)
    tbl.add_column("reason", no_wrap=False, overflow="fold")
    tbl.add_column("age", width=5, no_wrap=True)

    t.append("  LAST HOUR\n", style=f"bold {color}")

    for ev in reversed(recent):
        hook = ev.get("hook", "?")[:18]
        decision = ev.get("decision", "?")
        reason = ev.get("reason") or ev.get("target", "")[:50]
        age_s = now - ev.get("epoch", now)
        age = f"{int(age_s)}s" if age_s < 60 else f"{int(age_s/60)}m"
        icon, dc = DECISION_STYLE.get(decision, ("?", "white"))
        tbl.add_row(
            Text(icon, style=dc),
            Text(hook, style="white"),
            Text(decision, style=f"bold {dc}"),
            Text(reason[:55], style="grey70"),
            Text(age, style="grey42"),
        )

    if not recent:
        t.append("  No activity in the last hour.\n", style="grey30")
        border = color
    else:
        border = "red" if blocked else "yellow" if warned else color

    from rich.console import Group
    content = Group(t, tbl)
    return Panel(content, title=f"[{color}]GATE ACTIVITY — LIVE[/{color}]",
                 border_style=border, box=box.HEAVY_HEAD, padding=(0, 1))
