"""Behavioral Metrics — the 5 AI governance metrics: Integrity Index, Drift
Coefficient, Recurrence Rate, Verification Ratio, Stability Half-Life."""
import json
import math
import time
from pathlib import Path
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.console import Group
from rich import box
from .core import clr

SELF_CRITIQUE = Path.home() / ".mirrordna/self_critique.jsonl"
CC_EVENTS     = Path.home() / ".mirrordna/bus/cc_events.jsonl"
GATES         = Path.home() / ".mirrordna/bus/hook_decisions.jsonl"

READ_TOOLS  = {"Read", "Glob", "Grep"}
WRITE_TOOLS = {"Write", "Edit"}


def _load_critiques():
    if not SELF_CRITIQUE.exists():
        return []
    entries = []
    for line in SELF_CRITIQUE.read_text().splitlines():
        try:
            entries.append(json.loads(line.strip()))
        except Exception:
            pass
    return entries


def _compute_all():
    entries = _load_critiques()
    results = {}

    # ── 1. Integrity Index (0–100) ─────────────────────────────────────────
    # Score from risk_score logic (simplified): gate violations + recurring
    reads = writes = blocks = warns = 0
    cutoff = time.time() - 3600

    if CC_EVENTS.exists():
        lines = CC_EVENTS.read_text().splitlines()[-200:]
        for raw in lines:
            try:
                ev = json.loads(raw)
                t = ev.get("tool", "")
                if t in READ_TOOLS:  reads += 1
                if t in WRITE_TOOLS: writes += 1
            except Exception:
                pass

    if GATES.exists():
        for raw in GATES.read_text().splitlines():
            try:
                ev = json.loads(raw)
                if ev.get("epoch", 0) < cutoff:
                    continue
                v = ev.get("verdict", ev.get("decision", "")).lower()
                if "block" in v or "deny" in v: blocks += 1
                elif "warn" in v: warns += 1
            except Exception:
                pass

    rw_ratio = reads / writes if writes > 0 else 99
    ii = 100
    if rw_ratio < 1.0:
        ii -= min(30, int((1.0 - rw_ratio) * 40))
    elif rw_ratio < 2.0:
        ii -= 10
    ii -= min(25, blocks * 8)
    ii -= min(15, warns * 3)
    if entries:
        latest_recurring = len(entries[-1].get("recurring", []))
        if latest_recurring > 3:
            ii -= min(20, latest_recurring * 3)
        elif latest_recurring > 0:
            ii -= 5
    results["integrity_index"] = max(0, min(100, ii))

    # ── 2. Drift Coefficient (σ/μ) ─────────────────────────────────────────
    # Coefficient of variation of session scores. 0=stable, >0.3=drifting.
    scores = [e.get("score", 5) for e in entries if e.get("score") is not None]
    if len(scores) >= 2:
        mu = sum(scores) / len(scores)
        sigma = math.sqrt(sum((s - mu) ** 2 for s in scores) / len(scores))
        dc = sigma / mu if mu > 0 else 0.0
    elif scores:
        dc = 0.0
    else:
        dc = None
    results["drift_coefficient"] = dc

    # ── 3. Recurrence Rate ─────────────────────────────────────────────────
    # recurring_count / total_mistakes across all sessions.
    # High = same mistakes keep coming back. Target < 0.20.
    total_mistakes = sum(len(e.get("mistakes", [])) for e in entries)
    total_recurring = sum(len(e.get("recurring", [])) for e in entries)
    rr = total_recurring / total_mistakes if total_mistakes > 0 else 0.0
    results["recurrence_rate"] = rr
    results["total_mistakes"]  = total_mistakes
    results["total_recurring"] = total_recurring

    # ── 4. Verification Ratio ──────────────────────────────────────────────
    # reads / (reads + writes). Target ≥ 0.67 (2:1 read:write).
    total_rw = reads + writes
    vr = reads / total_rw if total_rw > 0 else None
    results["verification_ratio"] = vr
    results["reads"]  = reads
    results["writes"] = writes

    # ── 5. Stability Half-Life ─────────────────────────────────────────────
    # Avg sessions a recurring pattern persists before resolving.
    # Track each unique pattern (first 50 chars as key): first seen → last seen.
    pattern_spans = {}
    for i, e in enumerate(entries):
        for r in e.get("recurring", []):
            key = r[:50]
            if key not in pattern_spans:
                pattern_spans[key] = {"first": i, "last": i}
            else:
                pattern_spans[key]["last"] = i

    lifetimes = [v["last"] - v["first"] + 1 for v in pattern_spans.values()]
    shl = sum(lifetimes) / len(lifetimes) if lifetimes else None
    results["stability_half_life"] = shl
    results["pattern_count"] = len(pattern_spans)
    results["session_count"]  = len(entries)

    return results


def _grade(metric, value):
    """Return (color, label) for a metric value."""
    if value is None:
        return "grey30", "no data"
    if metric == "integrity_index":
        if value >= 80: return "green",  "CLEAN"
        if value >= 55: return "yellow", "WATCH"
        return "red", "RISK"
    if metric == "drift_coefficient":
        if value <= 0.15: return "green",  "stable"
        if value <= 0.30: return "yellow", "drifting"
        return "red", "unstable"
    if metric == "recurrence_rate":
        if value <= 0.15: return "green",  "good"
        if value <= 0.30: return "yellow", "moderate"
        return "red", "high"
    if metric == "verification_ratio":
        if value >= 0.67: return "green",  "good"
        if value >= 0.50: return "yellow", "ok"
        return "red", "low"
    if metric == "stability_half_life":
        if value <= 1.5: return "green",  "fast"
        if value <= 3.0: return "yellow", "moderate"
        return "red", "slow"
    return "grey50", "?"


def render(profile):
    color = clr(profile.get("color", "deep_sky_blue1"))
    m = _compute_all()

    metrics = [
        ("Integrity Index",    "integrity_index",    f"{m['integrity_index']:.0f}/100",
         "Risk score. Target ≥80."),
        ("Drift Coefficient",  "drift_coefficient",
         f"{m['drift_coefficient']:.3f}" if m["drift_coefficient"] is not None else "—",
         "σ/μ of session scores. Target ≤0.15."),
        ("Recurrence Rate",    "recurrence_rate",
         f"{m['recurrence_rate']:.2f}" if m["recurrence_rate"] is not None else "—",
         f"recurring/mistakes ({m['total_recurring']}/{m['total_mistakes']}). Target ≤0.20."),
        ("Verification Ratio", "verification_ratio",
         f"{m['verification_ratio']:.2f}" if m["verification_ratio"] is not None else "—",
         f"read/(read+write) ({m['reads']}/{m['reads']+m['writes']}). Target ≥0.67."),
        ("Stability Half-Life","stability_half_life",
         f"{m['stability_half_life']:.1f}s" if m["stability_half_life"] is not None else "—",
         f"{m['pattern_count']} patterns tracked. Target ≤1.5 sessions."),
    ]

    tbl = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    tbl.add_column("name",  width=20, no_wrap=True)
    tbl.add_column("value", width=10, no_wrap=True)
    tbl.add_column("grade", width=10, no_wrap=True)
    tbl.add_column("note",  no_wrap=False, overflow="fold")

    worst_color = "green"
    for name, key, val_str, note in metrics:
        mc, grade = _grade(key, m.get(key))
        if mc == "red":   worst_color = "red"
        elif mc == "yellow" and worst_color != "red": worst_color = "yellow"
        tbl.add_row(
            Text(name, style="grey70"),
            Text(val_str, style=f"bold {mc}"),
            Text(grade,   style=mc),
            Text(note,    style="grey42"),
        )

    header = Text()
    header.append(f"  {m['session_count']} sessions", style="bold white")
    header.append(f" · {m['pattern_count']} patterns tracked\n\n", style="grey50")

    frame = profile.get("_frame", 0)
    if worst_color == "red":
        border = "bright_red" if frame % 2 == 0 else "red"
    elif worst_color == "yellow":
        border = "yellow" if frame % 2 == 0 else "dark_orange"
    else:
        border = color

    return Panel(Group(header, tbl),
                 title=f"[{color}]BEHAVIORAL METRICS[/{color}]",
                 border_style=border, box=box.HEAVY_HEAD, padding=(0, 1))
