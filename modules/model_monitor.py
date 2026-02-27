"""Model Monitor — which AI models are running, loaded in RAM, and what's been used."""
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Group
from rich import box
from .core import clr

OLLAMA_BASE = "http://localhost:11434"
CC_EVENTS   = Path.home() / ".mirrordna/bus/cc_events.jsonl"

# API cost per 1M tokens (input) — update as prices change
API_COSTS = {
    "claude":  3.0,   # claude-sonnet tier
    "gpt":     2.5,
    "groq":    0.05,  # groq llama is very cheap
    "gemini":  0.075,
}


def _ollama_request(path: str):
    try:
        with urllib.request.urlopen(f"{OLLAMA_BASE}{path}", timeout=2) as r:
            return json.loads(r.read())
    except Exception:
        return None


def render(profile):
    color = clr(profile.get("color", "deep_sky_blue1"))

    t = Text()

    # ── LOADED IN RAM ──
    ps = _ollama_request("/api/ps")
    all_models = _ollama_request("/api/tags")

    t.append("  LOADED IN RAM\n", style=f"bold {color}")

    if ps is None:
        t.append("  Ollama not responding\n", style="red")
    elif not ps.get("models"):
        t.append("  No models loaded\n", style="grey50")
    else:
        ram_tbl = Table(show_header=False, box=None, padding=(0, 1), expand=True)
        ram_tbl.add_column("name",  no_wrap=True, overflow="fold")
        ram_tbl.add_column("ram",   width=8,  no_wrap=True)
        ram_tbl.add_column("proc",  width=6,  no_wrap=True)
        ram_tbl.add_column("until", width=6,  no_wrap=True)

        for m in ps["models"]:
            name  = m.get("name", "?")
            ram_mb = m.get("size", 0) // 1024 // 1024
            ram_gb = ram_mb / 1024
            proc  = "GPU" if "gpu" in str(m.get("details", {})).lower() else "CPU"
            pc    = "green" if proc == "GPU" else "yellow"

            # time until unloaded
            expires = m.get("expires_at", "")[:16]
            until_str = "∞"
            if expires:
                try:
                    from datetime import datetime, timezone
                    exp = datetime.fromisoformat(expires.replace("Z", "+00:00"))
                    diff = (exp - datetime.now(timezone.utc)).total_seconds()
                    if diff > 3600:
                        until_str = f"{int(diff/3600)}h"
                    elif diff > 0:
                        until_str = f"{int(diff/60)}m"
                    else:
                        until_str = "exp"
                except Exception:
                    pass

            ram_tbl.add_row(
                Text(name, style="cyan"),
                Text(f"{ram_gb:.1f}GB", style="grey70"),
                Text(proc, style=pc),
                Text(until_str, style="grey42"),
            )

    # ── ALL MODELS ON DISK ──
    cold_txt = Text(f"\n  ON DISK", style=f"bold {color}")
    loaded_names = set()
    if ps and ps.get("models"):
        loaded_names = {m["name"] for m in ps["models"]}

    if all_models and all_models.get("models"):
        total_gb = sum(m.get("size", 0) for m in all_models["models"]) / 1024**3
        cold_txt.append(f"  ({len(all_models['models'])} models, {total_gb:.0f}GB)\n", style="grey42")

        disk_tbl = Table(show_header=False, box=None, padding=(0, 1), expand=True)
        disk_tbl.add_column("status", width=2,  no_wrap=True)
        disk_tbl.add_column("name",   no_wrap=True, overflow="fold")
        disk_tbl.add_column("size",   width=6,  no_wrap=True)

        for m in all_models["models"]:
            name   = m.get("name", "?")
            size_gb = m.get("size", 0) / 1024**3
            hot    = name in loaded_names
            dot    = Text("▶", style="green") if hot else Text("·", style="grey30")
            nc     = "cyan" if hot else "grey50"
            disk_tbl.add_row(dot, Text(name, style=nc), Text(f"{size_gb:.1f}G", style="grey42"))
    else:
        cold_txt.append("  (unavailable)\n", style="grey30")
        disk_tbl = None

    # ── API MODELS IN USE ──
    api_txt = Text(f"\n  API CALLS THIS SESSION\n", style=f"bold {color}")
    session_id = None
    api_counts = {}
    if CC_EVENTS.exists():
        with open(CC_EVENTS) as f:
            lines = list(f)
        for raw in reversed(lines):
            try:
                ev = json.loads(raw)
                if not session_id and ev.get("session_id"):
                    session_id = ev["session_id"]
                if ev.get("session_id") != session_id:
                    continue
                tool   = ev.get("tool", "")
                target = ev.get("target", "").lower()
                # Detect which API is being called
                if tool == "Bash":
                    for api in ["groq", "openai", "anthropic", "gemini", "ollama"]:
                        if api in target:
                            api_counts[api] = api_counts.get(api, 0) + 1
                elif tool in ("WebFetch", "WebSearch"):
                    api_counts["web"] = api_counts.get("web", 0) + 1
            except Exception:
                pass

    # Always show Claude (current session is Claude)
    api_tbl = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    api_tbl.add_column("api",   width=14, no_wrap=True)
    api_tbl.add_column("calls", width=6,  no_wrap=True)
    api_tbl.add_column("note",  no_wrap=True)

    api_tbl.add_row(
        Text("claude-code", style="cyan"),
        Text("active", style="green"),
        Text("this session", style="grey42"),
    )
    for api, count in sorted(api_counts.items(), key=lambda x: -x[1]):
        api_tbl.add_row(
            Text(api, style="grey60"),
            Text(str(count), style="grey70"),
            Text("tool calls", style="grey30"),
        )

    if not api_counts:
        api_txt.append("  claude-code active  (no other API calls logged)\n", style="grey50")
        api_tbl = None

    parts = [t]
    if ps and ps.get("models"):
        parts.append(ram_tbl)
    parts += [cold_txt]
    if disk_tbl:
        parts.append(disk_tbl)
    parts.append(api_txt)
    if api_tbl:
        parts.append(api_tbl)

    return Panel(Group(*parts),
                 title=f"[{color}]MODEL MONITOR[/{color}]",
                 border_style=color, box=box.HEAVY_HEAD, padding=(0, 1))
