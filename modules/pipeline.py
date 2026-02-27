"""Pipeline module — founder deal pipeline stages."""
from pathlib import Path
from rich.panel import Panel
from rich.text import Text
from rich import box
from .core import clr, DASH_DIR, METRICS_FILE

PIPELINE_FILE = DASH_DIR / "pipeline.md"

STAGES = ["LEAD", "QUALIFIED", "PROPOSAL", "NEGOTIATION", "CLOSED"]
STAGE_COLORS = {
    "LEAD": "grey50",
    "QUALIFIED": "cyan",
    "PROPOSAL": "yellow",
    "NEGOTIATION": "bright_yellow",
    "CLOSED": "green",
}


def _load_pipeline():
    """Read pipeline.md — lines like: STAGE: Description ($value)"""
    if not PIPELINE_FILE.exists():
        return []
    items = []
    for line in PIPELINE_FILE.read_text().splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        items.append(s.lstrip("- ").strip())
    return items


def render(profile):
    color = clr(profile.get("color"))
    items = _load_pipeline()

    t = Text()

    # Load metrics for pipeline total
    pipeline_total = 0
    try:
        import yaml
        if METRICS_FILE.exists():
            m = yaml.safe_load(METRICS_FILE.read_text()) or {}
            pipeline_total = m.get("pipeline", 0)
            prospects = m.get("prospects", 0)
            if pipeline_total:
                t.append(f"  ${pipeline_total:,.0f}", style="bold green")
                t.append(f" pipeline  ", style="grey50")
                t.append(f"{prospects} prospects\n\n", style="grey70")
    except Exception:
        pass

    if items:
        for item in items[:10]:
            # Detect stage prefix
            stage = None
            for s in STAGES:
                if item.upper().startswith(s + ":") or item.upper().startswith(s + " "):
                    stage = s
                    break
            sc = STAGE_COLORS.get(stage, "grey50") if stage else "grey50"
            marker = f"[{sc}]▶[/{sc}]" if stage else "·"
            t.append_text(Text.from_markup(f"  {marker} "))
            t.append(f"{item}\n", style="grey85")
    else:
        t.append("  No pipeline entries.\n", style="grey50")
        t.append("  Add to ~/.mirrordash/pipeline.md\n", style="grey30")
        t.append("  Format: STAGE: Company ($value)\n", style="grey23")

    return Panel(t, title=f"[{color}]PIPELINE[/{color}]",
                 border_style=color, box=box.HEAVY_HEAD, padding=(0, 1))
