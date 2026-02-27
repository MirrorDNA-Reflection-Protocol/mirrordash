"""Vault Access — which vault/system files I'm reading, where my attention goes."""
import json
import re
import time
from collections import Counter
from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Group
from rich import box
from .core import clr

CC_EVENTS = Path.home() / ".mirrordna/bus/cc_events.jsonl"
HOME = Path.home()
VAULT = HOME / "MirrorDNA-Vault"
MIRRORDNA = HOME / ".mirrordna"


def _classify(path: str) -> tuple[str, str]:
    """Return (label, color) for a file path."""
    if ".mirrordna" in path:
        fname = Path(path).name
        return fname, "cyan"
    if "MirrorDNA-Vault" in path:
        parts = path.split("MirrorDNA-Vault/")[-1].split("/")
        return "/".join(parts[:2]), "magenta"
    if path.startswith("/tmp") or "factory" in path.lower():
        return Path(path).name, "yellow"
    return Path(path).name[:40], "grey60"


def render(profile):
    color = clr(profile.get("color", "deep_sky_blue1"))

    if not CC_EVENTS.exists():
        return Panel(Text("  No events logged.", style="grey50"),
                     title=f"[{color}]VAULT ACCESS[/{color}]",
                     border_style="grey30", box=box.SIMPLE_HEAD)

    reads = []
    writes = []
    cutoff = time.time() - 3600 * 6  # last 6h

    with open(CC_EVENTS) as f:
        for raw in f:
            try:
                ev = json.loads(raw)
                ts = ev.get("epoch") or ev.get("ts")
                tool = ev.get("tool", "")
                target = ev.get("target", "")
                if not target:
                    continue
                if tool in ("Read", "Glob", "Grep"):
                    reads.append(target)
                elif tool in ("Write", "Edit"):
                    writes.append(target)
            except Exception:
                pass

    # Top accessed
    read_counts = Counter(reads)
    write_counts = Counter(writes)

    t = Text()
    t.append(f"  {len(reads)} reads  {len(writes)} writes  (all time)\n\n", style="grey50")

    tbl = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    tbl.add_column("count", width=5, no_wrap=True)
    tbl.add_column("file",  no_wrap=False, overflow="fold")

    t.append("  MOST READ\n", style=f"bold {color}")
    for path, count in read_counts.most_common(8):
        label, fc = _classify(path)
        tbl.add_row(Text(f"{count}x", style="grey42"), Text(label, style=fc))

    wtbl = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    wtbl.add_column("count", width=5, no_wrap=True)
    wtbl.add_column("file",  no_wrap=False, overflow="fold")

    wt = Text("\n  MOST WRITTEN\n", style="bold yellow")
    for path, count in write_counts.most_common(6):
        label, fc = _classify(path)
        wtbl.add_row(Text(f"{count}x", style="grey42"), Text(label, style="yellow"))

    return Panel(Group(t, tbl, wt, wtbl),
                 title=f"[{color}]VAULT ACCESS[/{color}]",
                 border_style=color, box=box.HEAVY_HEAD, padding=(0, 1))
