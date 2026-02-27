"""Session Arc — horizontal timeline of this session's tool calls as colored blocks."""
import json
import time
from pathlib import Path
from rich.panel import Panel
from rich.text import Text
from rich import box
from .core import clr

CC_EVENTS = Path.home() / ".mirrordna/bus/cc_events.jsonl"

READ_TOOLS   = {"Read", "Glob", "Grep"}
WRITE_TOOLS  = {"Write", "Edit"}
EXEC_TOOLS   = {"Bash"}
WEB_TOOLS    = {"WebFetch", "WebSearch"}
AGENT_TOOLS  = {"Task", "TaskOutput"}


def _tool_color(tool: str) -> str:
    if tool in READ_TOOLS:   return "cyan"
    if tool in WRITE_TOOLS:  return "yellow"
    if tool in EXEC_TOOLS:   return "green"
    if tool in WEB_TOOLS:    return "blue"
    if tool in AGENT_TOOLS:  return "magenta"
    if "mobile" in tool.lower(): return "bright_magenta"
    return "grey42"


def _tool_char(tool: str) -> str:
    if tool in READ_TOOLS:   return "R"
    if tool in WRITE_TOOLS:  return "W"
    if tool in EXEC_TOOLS:   return "X"
    if tool in WEB_TOOLS:    return "N"
    if tool in AGENT_TOOLS:  return "A"
    if "mobile" in tool.lower(): return "M"
    return "·"


def render(profile):
    color = clr(profile.get("color", "deep_sky_blue1"))

    if not CC_EVENTS.exists():
        return Panel(Text("  No session events.", style="grey50"),
                     title=f"[{color}]SESSION ARC[/{color}]",
                     border_style="grey30", box=box.SIMPLE_HEAD)

    # Load current session — use last session_id or last 2 hours
    events = []
    cutoff = time.time() - 7200
    with open(CC_EVENTS) as f:
        all_lines = list(f)

    # Find current session_id from most recent event
    session_id = None
    for raw in reversed(all_lines):
        try:
            ev = json.loads(raw)
            sid = ev.get("session_id", "")
            if sid:
                session_id = sid
                break
        except Exception:
            pass

    # Collect this session's events
    for raw in all_lines:
        try:
            ev = json.loads(raw)
            if session_id and ev.get("session_id") == session_id:
                events.append(ev)
            elif not session_id and ev.get("epoch", 0) >= cutoff:
                events.append(ev)
        except Exception:
            pass

    t = Text()

    if not events:
        t.append("  No events this session.\n", style="grey50")
        return Panel(t, title=f"[{color}]SESSION ARC[/{color}]",
                     border_style=color, box=box.HEAVY_HEAD, padding=(0, 1))

    # Stats
    total = len(events)
    reads  = sum(1 for e in events if e.get("tool") in READ_TOOLS)
    writes = sum(1 for e in events if e.get("tool") in WRITE_TOOLS)
    execs  = sum(1 for e in events if e.get("tool") in EXEC_TOOLS)
    mobile = sum(1 for e in events if "mobile" in e.get("tool","").lower())

    t.append(f"  ", style="grey50")
    t.append(f"{total}", style="bold white")
    t.append(f" tool calls   ", style="grey50")
    t.append(f"R:", style="grey50"); t.append(f"{reads} ", style="bold cyan")
    t.append(f"W:", style="grey50"); t.append(f"{writes} ", style="bold yellow")
    t.append(f"X:", style="grey50"); t.append(f"{execs} ", style="bold green")
    if mobile:
        t.append(f"M:", style="grey50"); t.append(f"{mobile} ", style="bold bright_magenta")
    t.append("\n\n")

    # Timeline bar — compress to terminal width (max 80 chars)
    max_blocks = 76
    step = max(1, total // max_blocks)
    t.append("  ", style="")

    for i, ev in enumerate(events):
        if i % step != 0 and total > max_blocks:
            continue
        tool = ev.get("tool", "?")
        char = _tool_char(tool)
        c = _tool_color(tool)
        t.append(char, style=c)

    t.append("\n\n")

    # Legend
    t.append("  ", style="")
    for char, label, c in [("R","read","cyan"),("W","write","yellow"),("X","exec","green"),
                             ("N","web","blue"),("M","mobile","bright_magenta"),("A","agent","magenta")]:
        t.append(f"{char}", style=f"bold {c}")
        t.append(f"={label}  ", style="grey42")
    t.append("\n")

    # Phase detection — find where activity clusters
    if total >= 10:
        chunk = total // 3
        phases = [events[:chunk], events[chunk:2*chunk], events[2*chunk:]]
        phase_labels = ["EARLY", "MID", "LATE"]
        t.append("\n  PHASES   ", style="grey30")
        for phase, label in zip(phases, phase_labels):
            if not phase:
                continue
            dominant = {}
            for ev in phase:
                tool = ev.get("tool", "?")
                k = _tool_char(tool)
                dominant[k] = dominant.get(k, 0) + 1
            top = sorted(dominant.items(), key=lambda x: -x[1])[:2]
            top_str = "+".join(k for k, _ in top)
            t.append(f"{label}:{top_str}  ", style="grey50")
        t.append("\n")

    return Panel(t,
                 title=f"[{color}]SESSION ARC[/{color}]",
                 border_style=color, box=box.HEAVY_HEAD, padding=(0, 1))
