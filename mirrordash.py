#!/usr/bin/env python3
"""
MirrorDash — Modular terminal dashboard.
Usage: python3 mirrordash.py [--profile PROFILE] [--list]

Profiles live in ./profiles/*.yaml
Modules live in ./modules/*.py
Data goes in ~/.mirrordash/
"""

import argparse
import importlib
import sys
import time
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pip install pyyaml rich")
    sys.exit(1)

try:
    from rich.console import Console
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
MODULES_DIR = Path(__file__).parent / "modules"
DATA_DIR = Path.home() / ".mirrordash"
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
    """Import a module by name from the modules/ directory."""
    sys.path.insert(0, str(MODULES_DIR.parent))
    try:
        return importlib.import_module(f"modules.{name}")
    except ModuleNotFoundError:
        return None


def render_profile(profile: dict):
    """Render all modules for a profile into a 2-column layout."""
    module_names = profile.get("modules", [])
    panels = []

    for name in module_names:
        mod = load_module(name)
        if mod and hasattr(mod, "render"):
            try:
                panels.append(mod.render(profile))
            except Exception as e:
                panels.append(Panel(f"[red]{name}: {e}[/]", title=name))
        else:
            panels.append(Panel(
                f"[grey42]Module '{name}' not found.[/]\n"
                f"[grey30]Create modules/{name}.py with render(profile) -> Panel[/]",
                title=f"[grey30]{name}[/]",
                border_style="grey23",
                box=box.SIMPLE_HEAD
            ))

    cols = profile.get("columns", 2)
    return Columns(panels, equal=True, expand=True)


def header(profile: dict) -> Panel:
    color = profile.get("color", "bright_cyan")
    name = profile.get("name", "MirrorDash")
    desc = profile.get("description", "")
    from datetime import datetime
    now = datetime.now().strftime("%H:%M:%S")
    t = Text()
    t.append("◇ ", style=f"bold {color}")
    t.append(f"MIRRORDASH", style=f"bold {color}")
    t.append("  ─  ", style="grey30")
    t.append(name, style="white")
    t.append("  ─  ", style="grey30")
    t.append(desc, style="grey50")
    t.append(f"  {now}", style="grey42")
    return Panel(t, box=box.HORIZONTALS, border_style=color, padding=(0, 1))


def main():
    parser = argparse.ArgumentParser(description="MirrorDash — modular terminal dashboard")
    parser.add_argument("--profile", "-p", default="default", help="Profile name (default: default)")
    parser.add_argument("--list", "-l", action="store_true", help="List available profiles")
    parser.add_argument("--once", action="store_true", help="Render once and exit (no live mode)")
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
        console.print(header(profile))
        console.print(render_profile(profile))
        return

    with Live(console=console, refresh_per_second=1, screen=True) as live:
        while True:
            from rich.table import Table
            from rich.layout import Layout

            layout = Layout()
            layout.split_column(
                Layout(header(profile), size=3),
                Layout(render_profile(profile)),
            )
            live.update(layout)
            time.sleep(refresh)


if __name__ == "__main__":
    main()
