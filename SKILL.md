---
name: ralph
description: Self-improving goal loop using cron. Use /ralph start <goal> to begin.
metadata:
  {
    "openclaw": {
      "keywords": ["loop", "agent", "ralph", "arbos", "iteration", "self-improving", "cron"]
    }
  }
---

# Ralph Loop Skill

## Overview
A goal-tracking loop that runs automatically via cron. Each iteration generates a prompt, waits for work to be recorded, then advances.

## Concept
```
Goal + Cron → Run Step → Wait for Work → Record → Next Step → Repeat
```

## How It Works

1. **Set goal** with `/ralph start <goal>` — creates GOAL.md, STATE.md, sets up cron
2. **Cron runs** `/ralph run` every minute — generates prompt, increments iteration
3. **User does work** — based on the prompt
4. **Record progress** with `/ralph do <result>` or `/ralph continue <result>`
5. **State updates** — STATE.md tracks progress
6. **Loop continues** until DONE or max_iterations

## Key Features

- **Always auto** — cron runs automatically once started
- **Lock file** — prevents concurrent runs
- **Max iterations** — default 10, configurable
- **State persistence** — tracks progress across steps

## Commands

```
/ralph start <goal>  - Set goal, initialize state, start cron
/ralph run           - Generate next iteration prompt (cron calls this)
/ralph do <result>   - Record work done
/ralph continue <result> - Record AND advance to next step
/ralph next          - Advance to next iteration
/ralph prompt        - Show current prompt
/ralph status        - Check if running
/ralph logs [n]      - View recent runs
/ralph state         - Show current state
/ralph stop          - Halt and remove cron
/config              - Show settings
/config-set <k> <v>  - Update setting
/ralph help          - Show this help
/ralph improve       - Self-improvement suggestions
```

## Configuration

Edit `memory/.ralph_settings.json`:

```json
{
  "max_iterations": 10,
  "auto_frequency": "1m",
  "learn_from_usage": true
}
```

| Setting | Default | Description |
|---------|---------|-------------|
| `max_iterations` | 10 | Stop after N iterations |
| `auto_frequency` | "1m" | Cron frequency |
| `learn_from_usage` | true | Enable usage tracking |

## Workflow Example

```
/ralph start Build a todo app

# Cron runs /ralph run every minute...
# You do work based on the prompt...

/ralph continue "Created project structure and basic files"
/ralph continue "Added database schema and API endpoints"
/ralph continue "Completed feature - DONE"
# Loop stops when DONE is in result
```

## State File

`memory/STATE.md` tracks progress:
- Initial: "Goal set, ready to begin"
- After each `/ralph do`: "Step recorded: <summary>"
- On completion: "Goal marked as complete!"

## Lock File

`.running.lock` prevents concurrent runs. If a run is in progress, next cron tick waits.

## Success Criteria

Goal is achieved when:
- DONE or COMPLETE in `/ralph do` or `/ralph continue` result
- Max iterations reached
- User sends `/ralph stop`