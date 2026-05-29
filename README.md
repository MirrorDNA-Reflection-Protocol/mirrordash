# MirrorDash

**Real-time terminal dashboard that shows every decision your AI agent makes -- hook verdicts, tool calls, behavioral patterns, and integrity scoring.**

[![License: MIT](https://img.shields.io/badge/license-MIT-grey.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776ab.svg)](https://python.org)

---

AI agents are black boxes. You see inputs and outputs. Everything between -- which rules fired, what files were read before a write, whether the agent is repeating past mistakes -- is invisible.

MirrorDash makes it visible.

```
python3 mirrordash.py --profile glass
```

```
+---------------------------------------------------------------+
|  GLASS BOX -- AI TRANSPARENCY                                |
+---------------------------+-----------------------------------+
|                           |                                   |
|  BEHAVIORAL METRICS       |  GATE ACTIVITY                    |
|  Integrity: 72/100 [OK]  |  10:05:45  allow  Write  main.py  |
|  Read:Write  1.4x         |  10:05:43  warn   Bash   rm -rf  |
|  Gate violations: 0       |  10:05:40  allow  Read   cfg.yml  |
|  Recurring mistakes: 2    |                                   |
|                           +-----------------------------------+
|  MODEL MONITOR            |  SESSION ARC                      |
|  claude-opus-4  active    |  RRRXWWRRRXWWWRRR                 |
|  Tokens: 14.2k in / 3.1k |  ^^^^^^^^^^^^                     |
|                           |  Read-heavy start, write burst    |
|  MEMORY MAP               +-----------------------------------+
|  CONTINUITY.md    2m ago  |  TOOL FLOW                        |
|  MISTAKES.md      1h ago  |  Read   ||||||||||||  68%         |
|  bus/events.jsonl live    |  Write  |||||         27%         |
|                           |  Bash   ||            5%          |
+---------------------------+-----------------------------------+
```

## What It Monitors

MirrorDash reads from structured log files emitted by AI agent hooks (designed for Claude Code's PreToolUse and PostToolUse hooks, adaptable to other agent frameworks).

| Data Source | Contents |
|-------------|----------|
| `cc_events.jsonl` | Every tool call -- tool name, target file, timestamp |
| `hook_decisions.jsonl` | Gate decisions -- allow, warn, or block with reasoning |
| `self_critique.jsonl` | Session self-assessments -- score, mistakes, patterns |
| `MISTAKES.md` | Documented failure log with rule violations |

## Profiles

MirrorDash ships with six dashboard profiles. Each assembles a different set of modules for a different operational context.

| Profile | Purpose | Key Modules |
|---------|---------|-------------|
| `glass` | AI agent transparency | Integrity score, gate activity, session arc, mistake patterns, tool flow |
| `adhd` | Focus and energy tracking | Tasks, energy, loops, git status |
| `founder` | Product and company metrics | Metrics, queue, presence |
| `sysadmin` | Infrastructure monitoring | Services, git, system vitals |
| `teams` | Collaborative work | Presence, queue, metrics |
| `default` | General purpose | Configurable |

```bash
python3 mirrordash.py --list            # List available profiles
python3 mirrordash.py --profile glass   # Run a specific profile
python3 mirrordash.py --once            # Render once and exit (CI/scripting)
```

## The Integrity Score

The Glass Box profile computes a single 0-100 integrity score from four signals:

```
 72 / 100   [OK]

  ██████████████░░░░░░

  Read:Write 1.4x                       +0
  No gate violations                     +0
  2 recurring mistake patterns          -10
  Self-score trend: stable               +0
```

| Signal | What it measures |
|--------|-----------------|
| Read:Write ratio | An agent writing more than it reads is likely operating without sufficient context |
| Gate violations | Blocks and warnings from behavioral hooks in the last hour |
| Recurring mistakes | Patterns that appear across multiple sessions |
| Self-score trend | The agent's own reliability self-assessment over time |

## Modules

MirrorDash includes 26 modules. Each is a single Python file with one function: `render(profile) -> Panel`.

| Module | What it shows |
|--------|---------------|
| `behavioral_metrics` | Composite AI governance metrics |
| `risk_score` | 0-100 integrity score with breakdown |
| `gate_activity` | Live hook decisions as they happen |
| `session_arc` | Tool call timeline as a character sequence (`RRRXXWWW...`) |
| `critique_trend` | Score sparkline across sessions with recurring patterns |
| `rule_compliance` | Which behavioral rules fired, frequency, by which hooks |
| `mistake_patterns` | Documented mistakes aggregated by recurrence |
| `tool_flow` | Tool distribution bars and read:write ratio |
| `vault_access` | Most-read and most-written files |
| `memory_map` | Memory file ages, bus state, pending handoffs |
| `model_monitor` | Active model, token usage, latency |
| `net_activity` | Web fetches, searches, external calls |
| `services` | Service health status |
| `vitals` | System resource usage |
| `git` | Repository status |

## Installation

Two dependencies. No build step.

```bash
git clone https://github.com/MirrorDNA-Reflection-Protocol/mirrordash.git
cd mirrordash
pip install rich pyyaml
python3 mirrordash.py --profile glass --once
```

### Requirements

- Python 3.11+
- `rich>=13.0.0`
- `pyyaml>=6.0`

## Custom Profiles

Create a YAML file in `profiles/`:

```yaml
name: "My Profile"
description: "What this dashboard shows"
color: cyan
refresh: 10
layout:
  left:
    - risk_score
    - memory_map
  right:
    - session_arc
    - tool_flow
```

## Custom Modules

Each module is a single Python file in `modules/` that exports a `render` function:

```python
# modules/my_module.py
from rich.panel import Panel
from rich.text import Text
from .core import clr

def render(profile):
    color = clr(profile.get("color", "cyan"))
    content = Text("  Your content here", style="grey70")
    return Panel(content, title=f"[{color}]MY MODULE[/{color}]", border_style=color)
```

## Hook Integration

To feed data into MirrorDash, wire your AI agent's hooks to emit structured JSONL:

```json
{"ts": "2026-02-27T10:05:45Z", "tool": "Write", "type": "tool_use", "target": "/path/to/file.py"}
```

```json
{"ts": "2026-02-27T10:05:45Z", "hook": "deploy_gate", "verdict": "allow", "reason": "not destructive"}
```

See the Glass Box profile for the full data schema.

## Compliance

See [COMPLIANCE.md](COMPLIANCE.md) for control mappings against the EU AI Act, SOC 2 Type II, and ISO 27001:2022.

## Security

To report a vulnerability, see [SECURITY.md](SECURITY.md). Do not use public GitHub issues for security reports.

---

Built on [Rich](https://github.com/Textualize/rich). MIT License.

Built by [Active Mirror](https://activemirror.ai) -- governed AI for institutional work.
