"""Model Monitor — models loaded, weights, quantization, context, tokens, API calls."""
import json
import time
import urllib.request
from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Group
from rich import box
from .core import clr

OLLAMA_BASE = "http://localhost:11434"
CC_EVENTS   = Path.home() / ".mirrordna/bus/cc_events.jsonl"


def _ollama(path: str, body: dict = None):
    try:
        if body:
            data = json.dumps(body).encode()
            req  = urllib.request.Request(f"{OLLAMA_BASE}{path}", data=data,
                                          headers={"Content-Type": "application/json"})
        else:
            req = f"{OLLAMA_BASE}{path}"
        with urllib.request.urlopen(req, timeout=2) as r:
            return json.loads(r.read())
    except Exception:
        return None


def _quant_color(q: str) -> str:
    q = q.upper()
    if "Q8" in q or "F16" in q:  return "green"
    if "Q6" in q or "Q5" in q:   return "cyan"
    if "Q4" in q:                 return "yellow"
    return "grey50"


def render(profile):
    color = clr(profile.get("color", "deep_sky_blue1"))

    ps         = _ollama("/api/ps")
    all_models = _ollama("/api/tags")

    parts = []

    # ── HOT: LOADED IN RAM ──────────────────────────────────────────────────
    hot_txt = Text("  HOT — IN RAM\n", style=f"bold {color}")
    parts.append(hot_txt)

    if ps is None:
        parts.append(Text("  Ollama offline\n", style="red"))
    elif not ps.get("models"):
        parts.append(Text("  No models loaded\n", style="grey50"))
    else:
        hot_tbl = Table(show_header=False, box=None, padding=(0, 1), expand=True)
        hot_tbl.add_column("name",   no_wrap=True)
        hot_tbl.add_column("params", width=6,  no_wrap=True)
        hot_tbl.add_column("quant",  width=9,  no_wrap=True)
        hot_tbl.add_column("ctx",    width=5,  no_wrap=True)
        hot_tbl.add_column("ram",    width=7,  no_wrap=True)
        hot_tbl.add_column("proc",   width=4,  no_wrap=True)

        for m in ps["models"]:
            name   = m.get("name", "?")
            det    = m.get("details", {})
            params = det.get("parameter_size", "?")
            quant  = det.get("quantization_level", "?")
            ctx    = m.get("context_length", 0)
            ram_gb = m.get("size", 0) / 1024**3
            vram   = m.get("size_vram", 0)
            proc   = "GPU" if vram > 0 else "CPU"
            pc     = "green" if proc == "GPU" else "yellow"
            qc     = _quant_color(quant)

            ctx_str = f"{ctx//1024}K" if ctx >= 1024 else str(ctx)

            hot_tbl.add_row(
                Text(name, style="cyan"),
                Text(params, style="bright_white"),
                Text(quant,  style=qc),
                Text(ctx_str, style="grey60"),
                Text(f"{ram_gb:.1f}GB", style="grey70"),
                Text(proc,   style=pc),
            )
        parts.append(hot_tbl)

    # ── COLD: ALL ON DISK ───────────────────────────────────────────────────
    loaded_names = set()
    if ps and ps.get("models"):
        loaded_names = {m["name"] for m in ps["models"]}

    cold_txt = Text("\n  COLD — ON DISK\n", style=f"bold {color}")
    parts.append(cold_txt)

    if all_models and all_models.get("models"):
        total_gb = sum(m.get("size", 0) for m in all_models["models"]) / 1024**3
        sz_line = Text(f"  {len(all_models['models'])} models  {total_gb:.0f}GB total\n", style="grey42")
        parts.append(sz_line)

        cold_tbl = Table(show_header=False, box=None, padding=(0, 1), expand=True)
        cold_tbl.add_column("st",    width=2,  no_wrap=True)
        cold_tbl.add_column("name",  no_wrap=True)
        cold_tbl.add_column("params",width=6,  no_wrap=True)
        cold_tbl.add_column("quant", width=9,  no_wrap=True)
        cold_tbl.add_column("size",  width=6,  no_wrap=True)

        for m in all_models["models"]:
            name   = m.get("name", "?")
            det    = m.get("details", {})
            params = det.get("parameter_size", "?")
            quant  = det.get("quantization_level", "?")
            size_g = m.get("size", 0) / 1024**3
            hot    = name in loaded_names
            dot    = Text("▶", style="green") if hot else Text("·", style="grey30")
            nc     = "cyan" if hot else "grey50"
            qc     = _quant_color(quant) if hot else "grey30"
            cold_tbl.add_row(
                dot,
                Text(name,   style=nc),
                Text(params, style="grey60" if not hot else "white"),
                Text(quant,  style=qc),
                Text(f"{size_g:.1f}G", style="grey42"),
            )
        parts.append(cold_tbl)
    else:
        parts.append(Text("  (unavailable)\n", style="grey30"))

    # ── THIS SESSION: API CALLS ─────────────────────────────────────────────
    api_txt = Text("\n  THIS SESSION\n", style=f"bold {color}")
    parts.append(api_txt)

    session_id = None
    api_counts = {}
    mcp_counts = {}

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
                # MCP tool calls
                if tool.startswith("mcp__"):
                    parts_name = tool.split("__")
                    srv = parts_name[1] if len(parts_name) > 1 else tool
                    mcp_counts[srv] = mcp_counts.get(srv, 0) + 1
                # API calls via Bash
                elif tool == "Bash":
                    for api in ["groq", "openai", "anthropic", "gemini", "ollama"]:
                        if api in target:
                            api_counts[api] = api_counts.get(api, 0) + 1
                elif tool in ("WebFetch", "WebSearch"):
                    api_counts["web"] = api_counts.get("web", 0) + 1
            except Exception:
                pass

    sess_tbl = Table(show_header=False, box=None, padding=(0, 1), expand=True)
    sess_tbl.add_column("name",  width=18, no_wrap=True)
    sess_tbl.add_column("calls", width=5,  no_wrap=True)
    sess_tbl.add_column("type",  no_wrap=True)

    # Claude is always present
    sess_tbl.add_row(
        Text("claude-sonnet-4-6", style="cyan"),
        Text("active", style="green"),
        Text("primary model", style="grey42"),
    )
    for api, count in sorted(api_counts.items(), key=lambda x: -x[1]):
        sess_tbl.add_row(
            Text(api, style="grey60"),
            Text(str(count), style="yellow"),
            Text("api calls", style="grey30"),
        )
    for srv, count in sorted(mcp_counts.items(), key=lambda x: -x[1]):
        sess_tbl.add_row(
            Text(srv[:18], style="magenta"),
            Text(str(count), style="bright_magenta"),
            Text("mcp", style="grey30"),
        )
    parts.append(sess_tbl)

    return Panel(Group(*parts),
                 title=f"[{color}]MODEL MONITOR[/{color}]",
                 border_style=color, box=box.HEAVY_HEAD, padding=(0, 1))
