"""Mistake Patterns — documented failures from MISTAKES.md + critique recurring."""
import json
import re
from pathlib import Path
from rich.panel import Panel
from rich.text import Text
from rich import box
from .core import clr

MISTAKES_FILE = Path.home() / ".mirrordna/MISTAKES.md"
SELF_CRITIQUE = Path.home() / ".mirrordna/self_critique.jsonl"


def _load_mistakes():
    """Parse MISTAKES.md — return list of {title, rule, check} dicts."""
    if not MISTAKES_FILE.exists():
        return []
    text = MISTAKES_FILE.read_text()
    entries = []
    blocks = re.split(r'\n## ', text)
    for block in blocks[1:]:
        lines = block.strip().splitlines()
        title = lines[0].strip() if lines else "?"
        rule = next((l for l in lines if "Rule" in l), "")
        check = next((l for l in lines if l.strip().startswith("- Check:") or "check" in l.lower()), "")
        entries.append({"title": title, "rule": rule, "check": check})
    return entries


def _load_recurring():
    """Aggregate recurring patterns across all critique sessions."""
    if not SELF_CRITIQUE.exists():
        return {}
    counts = {}
    with open(SELF_CRITIQUE) as f:
        for raw in f:
            try:
                entry = json.loads(raw)
                for r in entry.get("recurring", []):
                    key = r[:60]
                    counts[key] = counts.get(key, 0) + 1
            except Exception:
                pass
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def render(profile):
    color = clr(profile.get("color", "deep_sky_blue1"))
    mistakes = _load_mistakes()
    recurring = _load_recurring()

    t = Text()

    if recurring:
        t.append("  RECURRING PATTERNS\n", style="bold red")
        for pattern, count in list(recurring.items())[:5]:
            t.append(f"  [{count}x] ", style="bold red")
            t.append(f"{pattern}\n", style="grey70")
        t.append("\n")

    if mistakes:
        t.append(f"  DOCUMENTED MISTAKES  ({len(mistakes)} total)\n", style=f"bold {color}")
        for m in mistakes[:6]:
            t.append(f"  ▸ {m['title'][:55]}\n", style="grey85")
            if m.get("rule"):
                t.append(f"    {m['rule'][:50]}\n", style="grey42")
            if m.get("check"):
                t.append(f"    → {m['check'][:55]}\n", style="grey30")
    else:
        t.append("  No documented mistakes found.\n", style="grey50")
        t.append("  MISTAKES.md at ~/.mirrordna/MISTAKES.md\n", style="grey30")

    border = "red" if recurring else color
    return Panel(t, title=f"[{color}]MISTAKE PATTERNS[/{color}]",
                 border_style=border, box=box.HEAVY_HEAD, padding=(0, 1))
