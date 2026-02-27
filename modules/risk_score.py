"""Risk Score — single integrity number computed from read:write ratio, gate fires, mistake recurrence."""
import json
import time
from pathlib import Path
from rich.panel import Panel
from rich.text import Text
from rich import box
from .core import clr

CC_EVENTS   = Path.home() / ".mirrordna/bus/cc_events.jsonl"
GATES       = Path.home() / ".mirrordna/bus/hook_decisions.jsonl"
CRITIQUES   = Path.home() / ".mirrordna/self_critique.jsonl"

READ_TOOLS  = {"Read", "Glob", "Grep"}
WRITE_TOOLS = {"Write", "Edit"}


def _compute(events_path, gates_path, critiques_path):
    score = 100  # start perfect, deduct
    signals = []

    # --- Signal 1: Read:Write ratio (last 200 tool calls) ---
    reads = writes = 0
    if events_path.exists():
        with open(events_path) as f:
            recent = list(f)[-200:]
        for raw in recent:
            try:
                ev = json.loads(raw)
                t = ev.get("tool", "")
                if t in READ_TOOLS:  reads += 1
                if t in WRITE_TOOLS: writes += 1
            except Exception:
                pass
    ratio = reads / writes if writes > 0 else 99
    if ratio < 1.0:
        deduct = min(30, int((1.0 - ratio) * 40))
        score -= deduct
        signals.append((f"Read:Write {ratio:.1f}x — writing without reading", "red", deduct))
    elif ratio < 2.0:
        score -= 10
        signals.append((f"Read:Write {ratio:.1f}x — borderline", "yellow", 10))
    else:
        signals.append((f"Read:Write {ratio:.1f}x", "green", 0))

    # --- Signal 2: Gate blocks/warns in last hour ---
    blocks = warns = 0
    cutoff = time.time() - 3600
    if gates_path.exists():
        with open(gates_path) as f:
            for raw in f:
                try:
                    ev = json.loads(raw)
                    epoch = ev.get("epoch", 0)
                    if epoch < cutoff:
                        continue
                    verdict = ev.get("verdict", ev.get("decision", "")).lower()
                    if "block" in verdict or "deny" in verdict:
                        blocks += 1
                    elif "warn" in verdict:
                        warns += 1
                except Exception:
                    pass
    if blocks > 0:
        deduct = min(25, blocks * 8)
        score -= deduct
        signals.append((f"{blocks} gate block(s) in last hour", "red", deduct))
    if warns > 0:
        deduct = min(15, warns * 3)
        score -= deduct
        signals.append((f"{warns} gate warn(s) in last hour", "yellow", deduct))
    if blocks == 0 and warns == 0:
        signals.append(("No gate violations", "green", 0))

    # --- Signal 3: Recurring mistake pattern count ---
    recurring_count = 0
    latest_score = None
    if critiques_path.exists():
        with open(critiques_path) as f:
            lines = [l.strip() for l in f if l.strip()]
        for raw in lines[-5:]:
            try:
                c = json.loads(raw)
                recurring_count += len(c.get("recurring", []))
                if latest_score is None:
                    latest_score = c.get("score", 5)
            except Exception:
                pass
    if recurring_count > 3:
        deduct = min(20, recurring_count * 3)
        score -= deduct
        signals.append((f"{recurring_count} recurring mistake patterns", "red", deduct))
    elif recurring_count > 0:
        score -= 5
        signals.append((f"{recurring_count} recurring pattern(s)", "yellow", 5))
    else:
        signals.append(("No recurring patterns", "green", 0))

    # --- Signal 4: Self-score trend ---
    if latest_score is not None and latest_score < 5:
        deduct = (5 - latest_score) * 3
        score -= deduct
        signals.append((f"Self-score {latest_score}/10", "yellow", deduct))
    elif latest_score is not None:
        signals.append((f"Self-score {latest_score}/10", "green", 0))

    return max(0, min(100, score)), signals


def render(profile):
    color = clr(profile.get("color", "deep_sky_blue1"))
    score, signals = _compute(CC_EVENTS, GATES, CRITIQUES)

    if score >= 80:
        sc, label = "green", "CLEAN"
    elif score >= 55:
        sc, label = "yellow", "WATCH"
    else:
        sc, label = "red", "RISK"

    t = Text()

    # Big number
    t.append(f"  {score:3d}", style=f"bold {sc}")
    t.append(" / 100   ", style="grey30")
    t.append(f"[{label}]\n\n", style=f"bold {sc}")

    # Integrity bar
    filled = score // 5  # 0-20 blocks
    t.append("  ", style="")
    t.append("█" * filled, style=sc)
    t.append("░" * (20 - filled), style="grey23")
    t.append("\n\n", style="")

    # Signal breakdown
    for msg, c, deduct in signals:
        marker = "·" if deduct == 0 else "▼"
        t.append(f"  {marker} ", style=c)
        t.append(msg, style="grey60" if deduct == 0 else "grey80")
        if deduct > 0:
            t.append(f"  -{deduct}", style=c)
        t.append("\n")

    frame = profile.get("_frame", 0)
    if sc == "red":
        border = "bright_red" if frame % 2 == 0 else "red"
    elif sc == "yellow":
        border = "yellow" if frame % 2 == 0 else "dark_orange"
    else:
        border = sc

    return Panel(t,
                 title=f"[{color}]INTEGRITY SCORE[/{color}]",
                 border_style=border, box=box.HEAVY_HEAD, padding=(0, 1))
