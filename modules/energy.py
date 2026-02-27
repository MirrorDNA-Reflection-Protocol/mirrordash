"""Energy module — time-of-day capacity + session timer."""
from datetime import datetime
from rich.panel import Panel
from rich.text import Text
from rich import box
from .core import clr, _bar

# Energy curve by hour (0-23), 0-10 scale
_CURVE = [2,1,1,1,2,3,5,7,9,10,9,8,6,5,6,7,8,9,7,5,4,3,2,2]

LABELS = {
    (0, 6):   ("SLEEP",   "grey42"),
    (6, 9):   ("WARM UP", "yellow"),
    (9, 12):  ("PEAK",    "green"),
    (12, 14): ("LUNCH",   "grey70"),
    (14, 17): ("SOLID",   "green"),
    (17, 20): ("WIND DOWN","yellow"),
    (20, 24): ("EVENING", "grey70"),
}


def _label(hour):
    for (start, end), (lbl, color) in LABELS.items():
        if start <= hour < end:
            return lbl, color
    return "ACTIVE", "white"


def render(profile):
    color = clr(profile.get("color"))
    now = datetime.now()
    hour = now.hour
    level = _CURVE[hour]
    lbl, lbl_color = _label(hour)

    t = Text()
    t.append(f"  {now.strftime('%H:%M')}  ", style="white")
    t.append(f"{lbl}\n\n", style=f"bold {lbl_color}")
    t.append("  CAPACITY  ", style="grey50")
    t.append(_bar(level, 10, width=20, color=lbl_color))
    t.append(f"  {level}/10\n", style="grey70")

    # Mini sparkline of the day
    t.append("\n  ")
    for h in range(24):
        lvl = _CURVE[h]
        ch = "▁▂▃▄▅▆▇█"[min(lvl, 7)]
        style = f"bold {color}" if h == hour else ("white" if lvl >= 7 else "grey42")
        t.append(ch, style=style)
    t.append("\n  0h" + " " * 8 + "12h" + " " * 7 + "24h\n", style="grey23")

    return Panel(t, title=f"[{color}]ENERGY[/{color}]",
                 border_style="grey30", box=box.SIMPLE_HEAD, padding=(0, 1))
