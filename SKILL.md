---
name: ralph
description: Self-improving agent loop that iteratively works toward a goal. Use /ralph start <goal> to begin.
metadata:
  {
    "openclaw": {
      "keywords": ["loop", "agent", "ralph", "arbos", "iteration", "self-improving"]
    }
  }
---

# Ralph Loop Skill

## Overview
A goal-tracking loop that iteratively works toward an objective with state persistence. Based on the Arbos pattern (MIT licensed), adapted for OpenClaw.

## Concept
```
Goal → Generate Prompt → Work → Record Result → Reflect → Repeat
```

## Files

- `ralph_loop.py` — Main skill logic
- `PROMPT.md` — Agent system prompt template
- `memory/` — Working memory (persists between iterations)

## How It Works

### Setup
1. User sets a goal with `/ralph start <goal>`
2. Goal is saved to `memory/GOAL.md`
3. Each iteration generates a prompt and tracks progress

### The Loop
Each iteration:
1. **Build prompt**: PROMPT.md + GOAL.md + STATE.md + INBOX.md + previous results
2. **Work**: Operator or subagent works on the goal
3. **Record**: Use `/ralph do <result>` to record progress
4. **Reflect**: Update STATE.md with what worked/didn't
5. **Repeat**: Until goal is achieved or max iterations

### State Files
| File | Purpose |
|------|---------|
| `memory/GOAL.md` | Objective (set by user) |
| `memory/STATE.md` | Working memory (persists between steps) |
| `memory/INBOX.md` | Messages (cleared after each step) |
| `memory/runs/` | Each iteration's output |
| `memory/.ralph_settings.json` | Configuration |

## Usage

```
/ralph start Build a Python script that analyzes stock prices

# Control the loop:
/ralph run              # Generate next iteration prompt
/ralph spawn            # Show subagent guidance with full prompt path
/ralph do <result>      # Record work done
/ralph continue <result> # Record result AND advance to next step (combined)
/ralph next             # Advance to next iteration
/ralph prompt           # Show current prompt
/ralph status           # Check if running (detailed view)
/ralph logs [n]         # View recent runs (default 5)
/ralph state            # Show current state
/ralph clear            # Clean up old runs
/ralph stop             # Halt
/ralph config           # Show settings
/ralph config-set <key> <value>  # Update setting
/ralph auto on|off      # Enable/disable auto-run mode (uses cron)
/ralph usage            # Show token usage stats
/ralph tune             # Auto-tune recommendations based on usage
/ralph help             # Show this help
```

## Workflow Example

```
/ralph start Improve the ralph-loop skill
/ralph run                    # Generates prompt for iteration 1
/ralph continue Fixed bugs   # Record result AND move to step 2
/ralph continue More fixes - DONE   # Goal completed
```

**Streamlined workflow:** Use `/ralph continue <result>` instead of separate do + next commands!

## Configuration

Edit `memory/.ralph_settings.json`:

```json
{
  "max_iterations": 10,
  "max_cost": null,
  "max_tokens_per_run": null,
  "model": "chutes/MiniMaxAI/MiniMax-M2.5-TEE",
  "timeout": 600,
  "max_retries": 3,
  "auto_mode": false,
  "auto_delay": 5,
  "auto_frequency": "1m",
  "learn_from_usage": true,
  "usage_stats": {}
}
```

| Setting | Default | Description |
|---------|---------|-------------|
| `max_iterations` | 10 | Stop after N iterations |
| `max_cost` | null | Stop after $N spent |
| `max_tokens_per_run` | null | Token budget per run |
| `model` | MiniMax-M2.5-TEE | Model to use |
| `timeout` | 600 | Seconds per iteration |
| `max_retries` | 3 | Retries on failure |
| `auto_mode` | false | Run automatically via cron |
| `auto_frequency` | "1m" | Cron frequency (e.g., "1m", "10m", "1h") |
| `learn_from_usage` | true | Enable usage tracking |
| `usage_stats` | {} | Token usage history |

## Key Differences from Arbos

| Arbos | Ralph Loop (OpenClaw) |
|-------|----------------------|
| Telegram | OpenClaw messages |
| Claude Code CLI | Built-in prompt generation |
| `context/` | `memory/` |
| pm2 process | OpenClaw session |
| while True loop | Commands + heartbeat |

## Success Criteria

Goal is achieved when:
- Agent signals DONE/COMPLETE in `/ralph do` result
- Max iterations reached
- User sends `/ralph stop`