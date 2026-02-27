"""Velocity module — git commit velocity across repos, last 7 days."""
from datetime import datetime, timedelta
from pathlib import Path
from rich.panel import Panel
from rich.text import Text
from rich import box
from .core import clr, _run

REPOS_DIR = Path.home() / "repos"


def _commits_last_7(repo_path):
    """Return list of (days_ago, msg) tuples for last 7 days."""
    out = _run(
        f"git -C '{repo_path}' log --oneline --since='7 days ago'"
        f" --format='%cr|%s' 2>/dev/null"
    )
    if not out:
        return []
    results = []
    for line in out.splitlines():
        parts = line.split("|", 1)
        if len(parts) == 2:
            results.append(parts)
    return results


def render(profile):
    color = clr(profile.get("color"))

    # Scan repos dir for git repos
    repos = []
    if REPOS_DIR.exists():
        for d in sorted(REPOS_DIR.iterdir()):
            if (d / ".git").exists():
                repos.append(d)

    # Commits per day (0=today, 6=6 days ago)
    day_counts = [0] * 7
    total_commits = 0
    recent_msgs = []

    for repo in repos[:20]:
        out = _run(
            f"git -C '{repo}' log --oneline --since='7 days ago'"
            f" --format='%ad|%s' --date=format:'%Y-%m-%d' 2>/dev/null"
        )
        if not out:
            continue
        for line in out.splitlines():
            parts = line.split("|", 1)
            if len(parts) == 2:
                try:
                    dt = datetime.strptime(parts[0].strip(), "%Y-%m-%d")
                    days_ago = (datetime.now() - dt).days
                    if 0 <= days_ago < 7:
                        day_counts[days_ago] += 1
                    total_commits += 1
                    if len(recent_msgs) < 5:
                        recent_msgs.append((parts[0].strip(), repo.name, parts[1].strip()))
                except Exception:
                    pass

    t = Text()
    t.append(f"  {total_commits}", style="bold white")
    t.append(" commits / 7 days\n\n", style="grey50")

    # Sparkline — day 6 (oldest) → day 0 (today)
    max_c = max(day_counts) or 1
    chars = "▁▂▃▄▅▆▇█"
    t.append("  ", style="")
    labels = []
    for i in range(6, -1, -1):
        c = day_counts[i]
        idx = min(int((c / max_c) * 7), 7)
        ch = chars[idx] if c > 0 else "·"
        style = f"bold {color}" if i == 0 else ("white" if c >= max_c * 0.7 else "grey42")
        t.append(ch, style=style)
        d = datetime.now() - timedelta(days=i)
        labels.append(d.strftime("%a"))
    t.append("\n  ")
    for lbl in labels:
        t.append(lbl[0], style="grey30")
    t.append("  ← today\n\n", style="grey23")

    # Recent commits
    if recent_msgs:
        t.append("  RECENT\n", style=f"bold {color}")
        for date, repo, msg in recent_msgs[:4]:
            t.append(f"  {date}  ", style="grey42")
            t.append(f"{repo[:10]:<10}", style=color)
            t.append(f" {msg[:30]}\n", style="grey70")

    if not repos:
        t.append("  No repos found in ~/repos/\n", style="grey30")

    return Panel(t, title=f"[{color}]VELOCITY[/{color}]",
                 border_style=color, box=box.HEAVY_HEAD, padding=(0, 1))
