"""Metrics module — founder KPIs (MRR, runway, pipeline)."""
from pathlib import Path
from rich.panel import Panel
from rich.text import Text
from rich import box
from .core import clr, METRICS_FILE

_DEFAULTS = {
    "mrr": 0, "mrr_delta": 0,
    "burn": 0, "runway_months": 0,
    "pipeline": 0, "prospects": 0,
}


def _load():
    if not METRICS_FILE.exists():
        return _DEFAULTS
    try:
        import yaml
        return {**_DEFAULTS, **yaml.safe_load(METRICS_FILE.read_text())}
    except Exception:
        return _DEFAULTS


def render(profile):
    color = clr(profile.get("color"))
    m = _load()

    t = Text()

    def stat(label, value, note="", color_val="white"):
        t.append(f"  {label:<10}", style="grey50")
        t.append(f"{value:<12}", style=f"bold {color_val}")
        t.append(f"{note}\n", style="grey42")

    stat("MRR", f"${m['mrr']:,.0f}",
         f"↑ +${m['mrr_delta']:,.0f}" if m['mrr_delta'] else "",
         "green" if m['mrr'] > 0 else "grey50")
    stat("BURN", f"${m['burn']:,.0f}/mo", "", "yellow")
    stat("RUNWAY", f"{m['runway_months']}mo",
         f"at current burn",
         "green" if m['runway_months'] > 6 else "red")
    stat("PIPELINE", f"${m['pipeline']:,.0f}",
         f"{m['prospects']} prospects", "cyan")

    if not METRICS_FILE.exists():
        t.append("\n  Set metrics in ~/.mirrordash/metrics.yaml\n", style="grey30")

    return Panel(t, title=f"[{color}]METRICS[/{color}]",
                 border_style=color, box=box.HEAVY_HEAD, padding=(0, 1))
