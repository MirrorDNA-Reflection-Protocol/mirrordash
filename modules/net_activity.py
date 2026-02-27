"""Net Activity — web fetches, searches, curl calls extracted from tool log."""
import json
import re
import time
from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Group
from rich import box
from .core import clr

CC_EVENTS = Path.home() / ".mirrordna/bus/cc_events.jsonl"

URL_RE = re.compile(r'https?://[^\s\'">{)\]]+')
CURL_RE = re.compile(r'curl\s+.*?(https?://[^\s\'">{)\]]+)', re.IGNORECASE)


def _extract_urls(target: str) -> list[str]:
    return URL_RE.findall(target)


def render(profile):
    color = clr(profile.get("color", "deep_sky_blue1"))

    if not CC_EVENTS.exists():
        return Panel(Text("  No events logged.", style="grey50"),
                     title=f"[{color}]NET ACTIVITY[/{color}]",
                     border_style="grey30", box=box.SIMPLE_HEAD)

    web_events = []
    curl_urls = []
    cutoff = time.time() - 86400

    with open(CC_EVENTS) as f:
        for raw in f:
            try:
                ev = json.loads(raw)
                tool = ev.get("tool", "")
                target = ev.get("target", "")
                epoch = ev.get("epoch", 0)

                if tool in ("WebFetch", "WebSearch"):
                    web_events.append({
                        "tool": tool,
                        "url": target[:80],
                        "age": time.time() - epoch if epoch else 0,
                    })
                elif tool == "Bash" and "curl" in target.lower():
                    for url in _extract_urls(target):
                        if not any(skip in url for skip in ["localhost", "localho", "127.0.0.1"]):
                            curl_urls.append({"url": url[:80], "age": time.time() - epoch if epoch else 0})
            except Exception:
                pass

    def age_str(s):
        if s < 60: return f"{int(s)}s"
        if s < 3600: return f"{int(s/60)}m"
        return f"{int(s/3600)}h"

    t = Text()

    # Web tool calls
    if web_events:
        t.append(f"  WEB TOOL CALLS  ({len(web_events)} total)\n", style=f"bold {color}")
        tbl = Table(show_header=False, box=None, padding=(0, 1), expand=True)
        tbl.add_column("tool",  width=12, no_wrap=True)
        tbl.add_column("url",   no_wrap=False, overflow="fold")
        tbl.add_column("age",   width=6,  no_wrap=True)
        for ev in reversed(web_events[-8:]):
            tc = "cyan" if ev["tool"] == "WebFetch" else "blue"
            tbl.add_row(
                Text(ev["tool"], style=tc),
                Text(ev["url"], style="grey60"),
                Text(age_str(ev["age"]), style="grey30"),
            )
    else:
        t.append("  No WebFetch/WebSearch calls logged.\n", style="grey50")
        tbl = None

    # Curl external calls
    ext_txt = Text()
    if curl_urls:
        ext_txt.append(f"\n  EXTERNAL CURL  ({len(curl_urls)} calls)\n", style="bold yellow")
        ctbl = Table(show_header=False, box=None, padding=(0, 1), expand=True)
        ctbl.add_column("url", no_wrap=False, overflow="fold")
        ctbl.add_column("age", width=6, no_wrap=True)
        for ev in reversed(curl_urls[-8:]):
            ctbl.add_row(Text(ev["url"], style="grey60"), Text(age_str(ev["age"]), style="grey30"))
        from rich.console import Group as G
        content = G(t, tbl, ext_txt, ctbl) if tbl else G(t, ext_txt, ctbl)
    else:
        ext_txt.append("\n  No external curl calls in log.\n", style="grey30")
        from rich.console import Group as G
        content = G(t, tbl, ext_txt) if tbl else G(t, ext_txt)

    total_external = len(web_events) + len(curl_urls)
    border = "yellow" if total_external > 10 else color
    title_suffix = f" ({total_external} external)" if total_external else ""

    return Panel(content,
                 title=f"[{color}]NET ACTIVITY{title_suffix}[/{color}]",
                 border_style=border, box=box.HEAVY_HEAD, padding=(0, 1))
