"""Rule Compliance — which rules fired in the last 24h."""
import json
import time
from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from .core import clr

HOOK_DECISIONS = Path.home() / ".mirrordna/bus/hook_decisions.jsonl"

RULES = {
    1: "No side-effectful test-fires",
    2: "No rebuilding what exists",
    3: "No exploring when told to execute",
    4: "No friction",
    5: "No 'ready' without verifying",
    7: "No apologies instead of fixes",
    8: "No factual claims from memory",
    9: "Run publish gate before publishing",
}

HOOK_TO_RULES = {
    "deploy_gate":          [1, 4],
    "logic_anchor":         [3],
    "anti_rationalization": [7],
    "fact_check":           [8],
    "duplicate_detector":   [2],
    "rabbit_hole":          [3],
    "rules_compliance":     [5],
    "publish_gate":         [9],
}


def render(profile):
    color = clr(profile.get("color", "deep_sky_blue1"))

    rule_hits = {r: {"warn": 0, "block": 0, "allow": 0} for r in RULES}
    hook_totals = {}

    if HOOK_DECISIONS.exists():
        cutoff = time.time() - 86400
        with open(HOOK_DECISIONS) as f:
            for raw in f:
                try:
                    ev = json.loads(raw)
                    if ev.get("epoch", 0) < cutoff:
                        continue
                    hook = ev.get("hook", "")
                    d = ev.get("decision", "allow")
                    hook_totals[hook] = hook_totals.get(hook, 0) + 1
                    for rn in HOOK_TO_RULES.get(hook, []):
                        if rn in rule_hits:
                            bucket = "block" if d in ("deny","block") else "warn" if d == "warn" else "allow"
                            rule_hits[rn][bucket] += 1
                except Exception:
                    pass

    tbl = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    tbl.add_column("num", width=7, no_wrap=True)
    tbl.add_column("status", width=14, no_wrap=True)
    tbl.add_column("rule", no_wrap=False, overflow="fold")

    active_rules = {rn: h for rn, h in rule_hits.items() if sum(h.values()) > 0}

    for num, desc in RULES.items():
        hits = rule_hits[num]
        total = sum(hits.values())
        if total == 0:
            continue
        if hits["block"] > 0:
            status = f"✗ {hits['block']} blocked"
            sc = "red"
        elif hits["warn"] > 0:
            status = f"! {hits['warn']} warned"
            sc = "yellow"
        else:
            status = f"· {hits['allow']} ok"
            sc = "green"
        tbl.add_row(
            Text(f"Rule {num}", style="grey50"),
            Text(status, style=sc),
            Text(desc, style="grey42"),
        )

    # Hook summary
    t = Text()
    t.append(f"  {len(active_rules)} rules active / 24h\n\n", style="grey50")

    htbl = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    htbl.add_column("hook", width=26, no_wrap=True)
    htbl.add_column("count", width=10, no_wrap=True)
    for hook, count in sorted(hook_totals.items(), key=lambda x: -x[1])[:6]:
        htbl.add_row(Text(hook, style="grey60"), Text(f"{count} fires", style="grey42"))

    any_block = any(h["block"] > 0 for h in rule_hits.values())
    any_warn  = any(h["warn"] > 0 for h in rule_hits.values())
    border = "red" if any_block else "yellow" if any_warn else color

    from rich.console import Group
    return Panel(Group(t, tbl, Text("\n  HOOKS\n", style=f"bold {color}"), htbl),
                 title=f"[{color}]RULE COMPLIANCE[/{color}]",
                 border_style=border, box=box.HEAVY_HEAD, padding=(0, 1))
