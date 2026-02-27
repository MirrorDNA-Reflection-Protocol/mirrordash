"""Shared utilities for all MirrorDash modules."""
import subprocess
import time
from datetime import datetime
from pathlib import Path

from rich import box
from rich.panel import Panel
from rich.text import Text

DASH_DIR = Path.home() / ".mirrordash"
TASKS_FILE = DASH_DIR / "tasks.md"
LOOPS_FILE = DASH_DIR / "loops.md"
METRICS_FILE = DASH_DIR / "metrics.yaml"
PRESENCE_FILE = DASH_DIR / "presence.json"


def clr(profile_color):
    return profile_color or "bright_cyan"


def _bar(value, max_val, width=14, fill="█", empty="░", color="green"):
    filled = int((value / max_val) * width) if max_val else 0
    filled = max(0, min(filled, width))
    t = Text()
    t.append(fill * filled, style=color)
    t.append(empty * (width - filled), style="grey23")
    return t


def _dot(ok: bool) -> str:
    return "[green]●[/]" if ok else "[red]●[/]"


def _run(cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, shell=True, text=True, timeout=3,
                                       stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def read_tasks():
    """Read tasks.md — returns (current, queue[], done[])."""
    if not TASKS_FILE.exists():
        return None, [], []
    lines = TASKS_FILE.read_text().splitlines()
    current, queue, done = None, [], []
    for line in lines:
        s = line.strip()
        if s.startswith("## NOW") or s.startswith("## CURRENT"):
            continue
        if s.startswith("> ") and current is None:
            current = s[2:].strip()
        elif s.startswith("- [ ] "):
            queue.append(s[6:])
        elif s.startswith("- [x] ") or s.startswith("- [X] "):
            done.append(s[6:])
    return current, queue, done


def read_loops():
    """Read loops.md — returns list of open loop strings."""
    if not LOOPS_FILE.exists():
        return []
    lines = LOOPS_FILE.read_text().splitlines()
    return [l.strip().lstrip("- ").strip() for l in lines
            if l.strip() and not l.strip().startswith("#")]
