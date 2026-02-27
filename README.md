# MirrorDash

**Modular terminal dashboard for AI agent transparency.**

The Glass Box profile shows what your AI agent is actually doing — every hook decision, tool call, file access, and behavioral pattern — in real time.

```
python3 mirrordash.py --profile glass
```

![MirrorDash Glass Box](docs/glass-preview.png)

---

## The problem

AI agents are black boxes. You see inputs and outputs. Everything in between — which rules fired, what files were read before a write, whether the agent is repeating past mistakes — is invisible.

MirrorDash makes it visible.

---

## Profiles

| Profile | For | What it shows |
|---------|-----|---------------|
| `glass` | AI transparency | Hook decisions, integrity score, mistake patterns, tool flow, memory state |
| `adhd` | Focus work | Tasks, energy, loops, git status |
| `founder` | Product/company | Metrics, queue, presence |
| `sysadmin` | Infrastructure | Services, git, vitals |
| `teams` | Collaborative work | Presence, queue, metrics |

```bash
python3 mirrordash.py --list          # show all profiles
python3 mirrordash.py --profile adhd  # run a specific profile
python3 mirrordash.py --once          # render once and exit
```

---

## Glass Box modules

| Module | What it shows |
|--------|---------------|
| `risk_score` | Single 0–100 integrity score: read:write ratio + gate violations + recurring mistakes |
| `gate_activity` | Live hook decisions (allow/warn/block) as they happen |
| `session_arc` | This session's tool calls as a character timeline: `RRRXXWWWXRW...` |
| `critique_trend` | Score sparkline across sessions, latest mistakes, recurring patterns |
| `rule_compliance` | Which behavioral rules fired, how many times, by which hooks |
| `mistake_patterns` | Documented mistakes aggregated by recurrence frequency |
| `tool_flow` | Tool distribution bars + read:write ratio |
| `vault_access` | Most-read and most-written files |
| `memory_map` | Memory file ages, bus state, pending handoffs |
| `net_activity` | Web fetches, searches, external curl calls |

---

## The integrity score

```
 56 / 100   [WATCH]

  ███████████░░░░░░░░░

  ▼ Read:Write 0.3x — writing without reading  -26
  · No gate violations
  ▼ 6 recurring mistake patterns  -18
  · Self-score 8/10
```

Computed from:
- **Read:Write ratio** — an agent writing more than it reads is likely hallucinating
- **Gate violations** — blocks and warnings from behavioral hooks in the last hour
- **Recurring mistakes** — patterns that appear session after session
- **Self-score trend** — the agent's own reliability assessment

---

## Data sources

MirrorDash reads from Claude Code hook output files:

| File | Contents |
|------|----------|
| `~/.mirrordna/bus/cc_events.jsonl` | PostToolUse log — every tool call with tool name, target, timestamp |
| `~/.mirrordna/bus/hook_decisions.jsonl` | PreToolUse decisions — allow/warn/block with reason |
| `~/.mirrordna/self_critique.jsonl` | Session self-assessments — score, mistakes, recurring patterns |
| `~/.mirrordna/MISTAKES.md` | Documented failure log with rule violations and check procedures |
| `~/.mirrordna/CONTINUITY.md` | Session context and memory files |

### Hook schema (cc_events.jsonl)

```json
{"ts": "2026-02-27T10:05:45Z", "epoch": 1772106345.0, "session_id": "abc123", "tool": "Write", "type": "tool_use", "target": "/path/to/file.py"}
```

### Hook schema (hook_decisions.jsonl)

```json
{"ts": "2026-02-27T10:05:45Z", "epoch": 1772106345.0, "hook": "deploy_gate", "verdict": "allow", "reason": "not destructive", "target": "bash command"}
```

Wire these with Claude Code's PostToolUse and PreToolUse hooks.

---

## Installation

```bash
git clone https://github.com/MirrorDNA-Reflection-Protocol/mirrordash
cd mirrordash
pip install -r requirements.txt
python3 mirrordash.py --profile glass --once
```

---

## Custom profiles

Create `profiles/yourprofile.yaml`:

```yaml
name: "My Profile"
description: "What this shows"
color: cyan
columns: 2
refresh: 10
wide:
  - session_arc
modules:
  - risk_score
  - session_arc
  - tool_flow
  - memory_map
```

Any module in `modules/` is available. Each module is a single Python file with one function: `render(profile) -> Panel`.

---

## Custom modules

```python
# modules/my_module.py
from rich.panel import Panel
from rich.text import Text
from .core import clr

def render(profile):
    color = clr(profile.get("color", "cyan"))
    t = Text("  Your content here", style="grey70")
    return Panel(t, title=f"[{color}]MY MODULE[/{color}]", border_style=color)
```

---

Built on [Rich](https://github.com/Textualize/rich). MIT License.
