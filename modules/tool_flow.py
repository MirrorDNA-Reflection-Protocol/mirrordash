"""Tool Flow — what tools I use, read/write ratio, last 10 actions."""
import json
import time
from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Group
from rich import box
from .core import clr

CC_EVENTS = Path.home() / ".mirrordna/bus/cc_events.jsonl"

READ_TOOLS  = {"Read", "Glob", "Grep"}
WRITE_TOOLS = {"Write", "Edit"}
EXEC_TOOLS  = {"Bash"}
WEB_TOOLS   = {"WebFetch", "WebSearch"}
MOBILE_TOOLS = {t for t in [] if "mobile" in t}  # populated dynamically


def render(profile):
    color = clr(profile.get("color", "deep_sky_blue1"))

    if not CC_EVENTS.exists():
        return Panel(Text("  No tool events logged yet.", style="grey50"),
                     title=f"[{color}]TOOL FLOW[/{color}]",
                     border_style="grey30", box=box.SIMPLE_HEAD)

    events = []
    cutoff = time.time() - 86400
    with open(CC_EVENTS) as f:
        for raw in f:
            try:
                ev = json.loads(raw)
                if ev.get("ts") or ev.get("epoch", 0) >= cutoff:
                    events.append(ev)
            except Exception:
                pass

    # Tool counts
    counts = {}
    recent = events[-200:] if len(events) > 200 else events
    for ev in recent:
        t = ev.get("tool", "?")
        counts[t] = counts.get(t, 0) + 1

    reads  = sum(counts.get(t, 0) for t in READ_TOOLS)
    writes = sum(counts.get(t, 0) for t in WRITE_TOOLS)
    execs  = sum(counts.get(t, 0) for t in EXEC_TOOLS)
    mobile = sum(v for k, v in counts.items() if "mobile" in k.lower())
    web    = sum(counts.get(t, 0) for t in WEB_TOOLS)
    total  = sum(counts.values())

    t = Text()

    # Summary ratios
    t.append("  TOOL DISTRIBUTION\n", style=f"bold {color}")
    def bar(n, total, width=16, c="cyan"):
        filled = int((n / total) * width) if total else 0
        txt = Text()
        txt.append("█" * filled, style=c)
        txt.append("░" * (width - filled), style="grey23")
        return txt

    rows = [
        ("Read/Glob/Grep", reads,  "cyan"),
        ("Write/Edit",     writes, "yellow"),
        ("Bash",           execs,  "green"),
        ("Mobile",         mobile, "magenta"),
        ("Web",            web,    "blue"),
    ]
    tbl = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    tbl.add_column("label", width=16, no_wrap=True)
    tbl.add_column("bar",   width=18, no_wrap=True)
    tbl.add_column("count", width=6,  no_wrap=True)
    for label, n, c in rows:
        if n == 0: continue
        tbl.add_row(Text(label, style="grey70"), bar(n, total, c=c), Text(str(n), style=f"bold {c}"))

    # Read:Write ratio
    ratio_txt = Text()
    if writes > 0:
        ratio = reads / writes
        rc = "green" if ratio >= 2 else "yellow" if ratio >= 1 else "red"
        ratio_txt.append(f"\n  Read:Write  ", style="grey50")
        ratio_txt.append(f"{ratio:.1f}x  ", style=f"bold {rc}")
        if ratio < 1:
            ratio_txt.append("⚠ writing more than reading", style="red")
        elif ratio < 2:
            ratio_txt.append("ok", style="yellow")
        else:
            ratio_txt.append("good", style="green")
    ratio_txt.append(f"\n  ", style="grey50")
    ratio_txt.append(f"{total}", style="bold white")
    ratio_txt.append(f" total tool calls logged\n", style="grey50")

    # Last 8 actions
    last_txt = Text()
    last_txt.append("\n  LAST ACTIONS\n", style=f"bold {color}")
    for ev in reversed(events[-8:]):
        tool = ev.get("tool", "?")[:12]
        target = ev.get("target", ev.get("command", ""))[:50]
        tc = "cyan" if tool in READ_TOOLS else "yellow" if tool in WRITE_TOOLS else \
             "green" if tool in EXEC_TOOLS else "grey50"
        last_txt.append(f"  {tool:<14}", style=tc)
        last_txt.append(f"{target}\n", style="grey40")

    return Panel(Group(t, tbl, ratio_txt, last_txt),
                 title=f"[{color}]TOOL FLOW[/{color}]",
                 border_style=color, box=box.HEAVY_HEAD, padding=(0, 1))
