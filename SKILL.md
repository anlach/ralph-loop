---
name: ralph
description: Self-improving agent loop that iteratively works toward a goal using subagents. Based on Arbos pattern. Use /ralph start <goal> to begin.
metadata:
  {
    "openclaw": {
      "keywords": ["loop", "agent", "ralph", "arbos", "iteration", "self-improving"]
    }
  }
---

# Ralph Loop Skill

## Overview
A self-improving agent loop that iteratively works toward a goal using subagents. Based on the Arbos pattern (MIT licensed), adapted for OpenClaw.

## Concept
```
GOAL.md → Subagent → Results → Reflect → Improved Approach → Loop
```

## Files

- `ralph_loop.py` — Main skill logic
- `PROMPT.md` — Agent system prompt template
- `memory/` — Working memory (persists between iterations)

## How It Works

### Setup
1. User sets a goal with `/ralph start <goal>`
2. Goal is saved to `memory/GOAL.md`
3. Each iteration spawns a subagent with full context

### The Loop
Each iteration:
1. **Build prompt**: PROMPT.md + GOAL.md + STATE.md + INBOX.md + previous results
2. **Run subagent**: Spawn coding subagent to work toward goal
3. **Reflect**: Analyze results, identify improvements
4. **Update STATE.md**: Document what worked/didn't for next iteration
5. **Repeat**: Until goal is achieved or max iterations

### State Files
| File | Purpose |
|------|---------|
| `memory/GOAL.md` | Objective (set by user) |
| `memory/STATE.md` | Working memory (persists between steps) |
| `memory/INBOX.md` | Messages from user (cleared after each step) |
| `memory/runs/` | Each iteration's output |
| `memory/.ralph_settings.json` | Configuration |

## Usage

```
/ralph start Build a Python script that analyzes stock prices

# Then control the loop:
/ralph run     # Execute one iteration
/ralph auto on # Enable auto-run mode (runs automatically)
/ralph auto off # Disable auto-run mode
/ralph status  # Check if running
/ralph stop    # Halt
/ralph config  # Show settings
/ralph help    # Show help
```

## Configuration

Edit `memory/.ralph_settings.json`:

```json
{
  "max_iterations": 10,
  "max_cost": null,
  "model": "chutes/MiniMaxAI/MiniMax-M2.5-TEE",
  "timeout": 600,
  "max_retries": 3,
  "auto_mode": false,
  "auto_delay": 5
}
```

| Setting | Default | Description |
|---------|---------|-------------|
| `max_iterations` | 10 | Stop after N iterations |
| `max_cost` | null | Stop after $N spent |
| `model` | MiniMax-M2.5-TEE | Model to use |
| `timeout` | 600 | Seconds per iteration |
| `max_retries` | 3 | Retries on failure |
| `auto_mode` | false | Run automatically on heartbeat |
| `auto_delay` | 5 | Seconds between iterations |

## Key Differences from Arbos

| Arbos | Ralph Loop (OpenClaw) |
|-------|----------------------|
| Telegram | OpenClaw messages |
| Claude Code CLI | `sessions_spawn` subagent |
| `context/` | `memory/` |
| pm2 process | OpenClaw session |
| Encrypted .env | OpenClaw credential storage |
| while True loop | Heartbeat + commands |

## Agent Instructions

The subagent receives instructions from `PROMPT.md`:
- Design systems, not one-offs
- Use STATE.md for continuity between iterations
- Signal completion with "DONE" or "COMPLETE"

## Success Criteria

Goal is achieved when:
- Agent signals DONE/COMPLETE
- Max iterations reached
- User sends `/ralph stop`