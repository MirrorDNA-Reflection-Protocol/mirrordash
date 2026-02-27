"""Vitals module — CPU, RAM, disk."""
import subprocess
from rich.panel import Panel
from rich.text import Text
from rich import box
from .core import clr, _bar, _run


def _cpu():
    try:
        out = _run("top -l 1 -n 0 | grep 'CPU usage'")
        if out:
            import re
            m = re.search(r'([\d.]+)% user', out)
            if m:
                return float(m.group(1))
    except Exception:
        pass
    try:
        import psutil
        return psutil.cpu_percent(interval=0.1)
    except Exception:
        return 0.0


def _ram():
    try:
        import psutil
        m = psutil.virtual_memory()
        return m.percent, m.used // (1024**3), m.total // (1024**3)
    except Exception:
        return 0.0, 0, 0


def _disk():
    try:
        import psutil
        d = psutil.disk_usage('/')
        return d.percent, d.used // (1024**3), d.total // (1024**3)
    except Exception:
        return 0.0, 0, 0


def render(profile):
    color = clr(profile.get("color"))
    cpu = _cpu()
    ram_pct, ram_used, ram_total = _ram()
    disk_pct, disk_used, disk_total = _disk()

    def bar_color(pct):
        return "red" if pct > 85 else "yellow" if pct > 60 else "green"

    t = Text()
    t.append("  CPU  ", style="grey70")
    t.append(_bar(cpu, 100, width=18, color=bar_color(cpu)))
    t.append(f"  {cpu:.0f}%\n", style="grey85")

    t.append("  RAM  ", style="grey70")
    t.append(_bar(ram_pct, 100, width=18, color=bar_color(ram_pct)))
    t.append(f"  {ram_used}/{ram_total}G\n", style="grey85")

    t.append("  DISK ", style="grey70")
    t.append(_bar(disk_pct, 100, width=18, color=bar_color(disk_pct)))
    t.append(f"  {disk_used}/{disk_total}G\n", style="grey85")

    return Panel(t, title=f"[{color}]VITALS[/{color}]",
                 border_style="grey30", box=box.SIMPLE_HEAD, padding=(0, 1))
