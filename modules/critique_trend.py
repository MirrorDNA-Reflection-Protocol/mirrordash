"""Critique Trend — self-assessment scores across sessions."""
import json
from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from .core import clr

SELF_CRITIQUE = Path.home() / ".mirrordna/self_critique.jsonl"

def _sc(s):
    if s is None: return "grey30"
    if s >= 7: return "green"
    if s >= 4: return "yellow"
    return "red"

def _ch(s):
    if s is None: return "?"
    return "▁▂▃▄▅▆▇█"[min(int(s)-1, 7)] if s else "▁"

def render(profile):
    color = clr(profile.get("color", "deep_sky_blue1"))

    if not SELF_CRITIQUE.exists():
        return Panel(Text("  No self-critique entries yet.", style="grey50"),
                     title=f"[{color}]CRITIQUE TREND[/{color}]",
                     border_style="grey30", box=box.SIMPLE_HEAD)

    entries = []
    with open(SELF_CRITIQUE) as f:
        for line in f:
            try:
                entries.append(json.loads(line.strip()))
            except Exception:
                pass

    if not entries:
        return Panel(Text("  No entries.", style="grey50"),
                     title=f"[{color}]CRITIQUE TREND[/{color}]",
                     border_style="grey30", box=box.SIMPLE_HEAD)

    scores = [e.get("score") for e in entries]
    latest = scores[-1]
    avg = sum(s for s in scores if s) / max(len([s for s in scores if s]), 1)
    last = entries[-1]
    recurring = last.get("recurring", [])

    t = Text()

    # Sparkline
    t.append("  SCORE HISTORY  ", style="grey50")
    for s in scores[-20:]:
        t.append(_ch(s), style=_sc(s))
    t.append(f"  {latest}/10 ", style=f"bold {_sc(latest)}")
    t.append(f"avg {avg:.1f}\n\n", style="grey50")

    # Latest session
    t.append(f"  {last.get('date','?')}  ", style="grey42")
    t.append(f"{last.get('session_id','')[:24]}\n", style="grey30")

    for mistake in last.get("mistakes", [])[:3]:
        t.append("  · ", style="yellow")
        t.append(f"{mistake[:68]}\n", style="grey70")

    if recurring:
        t.append("\n  RECURRING\n", style="bold red")
        for r in recurring[:2]:
            t.append("  !! ", style="red")
            t.append(f"{r[:65]}\n", style="grey70")

    for a in last.get("automated", [])[:2]:
        t.append("  ✓ ", style="green")
        t.append(f"{a[:65]}\n", style="grey50")

    border = "red" if recurring else "yellow" if last.get("mistakes") else color
    return Panel(t, title=f"[{color}]CRITIQUE TREND[/{color}]",
                 border_style=border, box=box.HEAVY_HEAD, padding=(0, 1))
