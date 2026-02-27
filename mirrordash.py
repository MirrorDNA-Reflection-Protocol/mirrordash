#!/usr/bin/env python3
"""
MirrorDash — Modular terminal dashboard.
Usage: python3 mirrordash.py [--profile PROFILE] [--list] [--once]
"""

import argparse
import importlib
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pip install pyyaml rich")
    sys.exit(1)

try:
    from rich.console import Console, Group
    from rich.layout import Layout
    from rich.live import Live
    from rich.columns import Columns
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
except ImportError:
    print("pip install rich")
    sys.exit(1)

PROFILES_DIR = Path(__file__).parent / "profiles"
MODULES_DIR  = Path(__file__).parent / "modules"
DATA_DIR     = Path.home() / ".mirrordash"
DATA_DIR.mkdir(exist_ok=True)

console = Console()


def load_profile(name: str) -> dict:
    path = PROFILES_DIR / f"{name}.yaml"
    if not path.exists():
        console.print(f"[red]Profile not found:[/] {name}")
        console.print(f"Available: {', '.join(p.stem for p in PROFILES_DIR.glob('*.yaml'))}")
        sys.exit(1)
    return yaml.safe_load(path.read_text())


def load_module(name: str):
    sys.path.insert(0, str(MODULES_DIR.parent))
    try:
        return importlib.import_module(f"modules.{name}")
    except ModuleNotFoundError:
        return None


def render_module(name: str, profile: dict) -> Panel:
    mod = load_module(name)
    if mod and hasattr(mod, "render"):
        try:
            return mod.render(profile)
        except Exception as e:
            return Panel(Text(f"{name}: {e}", style="red"), title=name, border_style="red")
    return Panel(
        Text(f"modules/{name}.py not found", style="grey42"),
        title=f"[grey30]{name}[/]", border_style="grey23", box=box.SIMPLE_HEAD
    )


def build_layout(profile: dict) -> Layout:
    """
    Build a ratio-based Layout that fills the terminal.

    Profile can define a 'layout' key:
      layout:
        left:   [module, module, ...]   # ratio=2 column
        right:  [module, [mod, mod], ...]  # ratio=3 column, list = split_row
      left_ratio: 2
      right_ratio: 3

    Falls back to auto 2-column grid if no layout key.
    """
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
    )

    cfg_layout = profile.get("layout")

    if cfg_layout:
        # Structured 2-column layout
        left_ratio  = profile.get("left_ratio", 2)
        right_ratio = profile.get("right_ratio", 3)

        layout["body"].split_row(
            Layout(name="left",  ratio=left_ratio),
            Layout(name="right", ratio=right_ratio),
        )

        def build_column(col_name, items):
            if not items:
                return
            layout[col_name].split_column(
                *[Layout(name=f"{col_name}_{i}") for i in range(len(items))]
            )
            for i, item in enumerate(items):
                cell = layout[f"{col_name}_{i}"]
                if isinstance(item, list):
                    # Split row within column
                    cell.split_row(*[Layout(name=f"{col_name}_{i}_{j}") for j in range(len(item))])
                    for j, mod_name in enumerate(item):
                        layout[f"{col_name}_{i}_{j}"].update(render_module(mod_name, profile))
                else:
                    cell.update(render_module(item, profile))

        build_column("left",  cfg_layout.get("left",  []))
        build_column("right", cfg_layout.get("right", []))

    else:
        # Auto grid — equal columns
        modules = profile.get("modules", [])
        wide    = set(profile.get("wide", []))
        cols    = profile.get("columns", 2)

        # Group into rows
        rows = []
        buf  = []
        for name in modules:
            if name in wide:
                if buf:
                    rows.append(buf); buf = []
                rows.append([name])
            else:
                buf.append(name)
                if len(buf) == cols:
                    rows.append(buf); buf = []
        if buf:
            rows.append(buf)

        if not rows:
            layout["body"].update(Panel("No modules."))
            return layout

        layout["body"].split_column(
            *[Layout(name=f"row_{i}") for i in range(len(rows))]
        )
        for i, row in enumerate(rows):
            if len(row) == 1:
                layout[f"row_{i}"].update(render_module(row[0], profile))
            else:
                layout[f"row_{i}"].split_row(
                    *[Layout(name=f"row_{i}_col_{j}") for j in range(len(row))]
                )
                for j, name in enumerate(row):
                    layout[f"row_{i}_col_{j}"].update(render_module(name, profile))

    return layout


# Pulse frames — cycles through on every animation tick
_PULSE_FRAMES = ["◇", "◈", "⟡", "◆", "⟡", "◈"]
# ECG trace — scrolls across header
_ECG = "─────────────────╱╲──────────────────────────────────────────────────"


def make_header(profile: dict, frame: int = 0) -> Panel:
    color  = profile.get("color", "bright_cyan")
    now    = datetime.now().strftime("%H:%M:%S")
    pulse  = _PULSE_FRAMES[frame % len(_PULSE_FRAMES)]
    # Scrolling ECG
    ecg_w  = 28
    offset = frame % len(_ECG)
    ecg    = (_ECG * 2)[offset:offset + ecg_w]

    t = Text()
    t.append(f"{pulse} MIRRORDASH", style=f"bold {color}")
    t.append("  ─  ", style="grey30")
    t.append(profile.get("name", ""), style="white")
    t.append("  ", style="")
    t.append(ecg, style=f"dim {color}")
    t.append("  ", style="")
    t.append(profile.get("description", ""), style="grey50")
    t.append(f"  {now}", style="grey60")
    return Panel(t, box=box.HORIZONTALS, border_style=color, padding=(0, 1))


def render_once(profile: dict):
    """Print all modules stacked — natural height, scrollable."""
    modules = profile.get("modules", [])
    wide    = set(profile.get("wide", []))
    cols    = profile.get("columns", 2)
    rows    = []
    buf     = []

    # Also handle structured layout key
    cfg_layout = profile.get("layout")
    if cfg_layout:
        all_mods = []
        for side in ("left", "right"):
            for item in cfg_layout.get(side, []):
                if isinstance(item, list):
                    all_mods.extend(item)
                else:
                    all_mods.append(item)
        modules = all_mods

    for name in modules:
        if name in wide:
            if buf:
                rows.append(Columns([render_module(m, profile) for m in buf], equal=True, expand=True))
                buf = []
            rows.append(render_module(name, profile))
        else:
            buf.append(name)
            if len(buf) == cols:
                rows.append(Columns([render_module(m, profile) for m in buf], equal=True, expand=True))
                buf = []
    if buf:
        rows.append(Columns([render_module(m, profile) for m in buf], equal=True, expand=True))

    console.print(make_header(profile, frame=0))
    for row in rows:
        console.print(row)


def main():
    parser = argparse.ArgumentParser(description="MirrorDash")
    parser.add_argument("--profile", "-p", default="default")
    parser.add_argument("--list",    "-l", action="store_true")
    parser.add_argument("--once",          action="store_true")
    args = parser.parse_args()

    if args.list:
        console.print("\n[bold]Available profiles:[/]\n")
        for p in sorted(PROFILES_DIR.glob("*.yaml")):
            cfg = yaml.safe_load(p.read_text())
            console.print(f"  [cyan]{p.stem:<15}[/] {cfg.get('name','')} — {cfg.get('description','')}")
        console.print()
        return

    profile = load_profile(args.profile)
    refresh = profile.get("refresh", 15)

    if args.once:
        render_once(profile)
        return

    with Live(console=console, refresh_per_second=4, screen=True) as live:
        frame        = 0
        last_rebuild = 0.0

        while True:
            now = time.time()
            profile["_frame"] = frame

            # Rebuild data panels every `refresh` seconds
            if now - last_rebuild >= refresh:
                layout       = build_layout(profile)
                last_rebuild = now

            # Always update header (drives pulse + ECG animation)
            layout["header"].update(make_header(profile, frame))
            live.update(layout)

            frame += 1
            time.sleep(0.25)   # 4 fps animation tick


if __name__ == "__main__":
    main()
