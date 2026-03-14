# Ralph Loop Skill - Requirements Document

## Overview

A self-improving agent loop skill for OpenClaw that iteratively works toward a goal using subagents. Based on the Arbos pattern (MIT licensed).

## Motivation

The Ralph Loop pattern from Arbos enables:
- **Continuous improvement** — Each iteration builds on the last
- **System design over one-off solutions** — Build something that gets better
- **Operator control** — Human sets goals, agent executes
- **Persistence** — State survives between iterations

## Use Cases

1. **Complex coding tasks** — Build systems that evolve over time
2. **Research loops** — Explore solutions, reflect, improve
3. **Automated workflows** — Multi-step processes that adapt

## Functional Requirements

### 1. Goal Management

| Requirement | Description |
|-------------|-------------|
| F1.1 | Set goal via message command |
| F1.2 | Clear goal to stop the loop |
| F1.3 | Goal persists in `memory/GOAL.md` |
| F1.4 | Detect goal changes and reset iteration counter |

### 2. State Management

| Requirement | Description |
|-------------|-------------|
| F2.1 | Maintain `memory/STATE.md` for working memory |
| F2.2 | State persists between iterations |
| F2.3 | Agent can read/write state |
| F2.4 | Clear state when goal is cleared |

### 3. Inbox System

| Requirement | Description |
|-------------|-------------|
| F3.1 | Store new messages in `memory/INBOX.md` |
| F3.2 | Inbox is consumed (cleared) after each iteration |
| F3.3 | Operator can send messages between iterations |

### 4. Loop Execution

| Requirement | Description |
|-------------|-------------|
| F4.1 | Spawn subagent with full context each iteration |
| F4.2 | Include GOAL + STATE + INBOX + previous results in prompt |
| F4.3 | Run iterations back-to-back on success |
| F4.4 | Apply exponential backoff on failure (2, 4, 8... max 120s) |
| F4.5 | Stop when goal is achieved (agent signals DONE) |
| F4.6 | Stop when max iterations reached |
| F4.7 | Stop when max cost exceeded |

### 5. Run History

| Requirement | Description |
|-------------|-------------|
| F5.1 | Save each iteration's output to `memory/runs/<timestamp>/` |
| F5.2 | Include prompt, output, and metadata in run directory |
| F5.3 | Limit stored runs (e.g., last 50) |

### 6. Configuration

| Requirement | Description |
|-------------|-------------|
| F6.1 | Configurable max iterations (default: 10) |
| F6.2 | Configurable max cost (default: unlimited) |
| F6.3 | Configurable model |
| F6.4 | Configurable notify channel for updates |

### 7. Operator Interface

| Requirement | Description |
|-------------|-------------|
| F7.1 | `/ralph start <goal>` — Set goal and begin |
| F7.2 | `/ralph stop` — Clear goal and halt |
| F7.3 | `/ralph run` — Execute one iteration |
| F7.4 | `/ralph status` — Check if running |
| F7.5 | `/ralph config` — Show settings |
| F7.6 | Send messages to agent between iterations |

## Non-Functional Requirements

| Requirement | Description |
|-------------|-------------|
| NF1.1 | Each iteration runs as isolated subagent |
| NF1.2 | No memory between iterations (fresh context) |
| NF1.3 | Agent must write to STATE.md for continuity |
| NF1.4 | Security: redact API keys from outputs |

## Architecture

### File Structure
```
skills/ralph-loop/
├── SKILL.md           # Overview & usage
├── REQUIREMENTS.md    # This document
├── ralph_loop.py      # Main skill logic
├── PROMPT.md          # Agent system prompt
└── config.py          # Configuration handling
```

### Data Flow
```
Operator Message
       │
       ▼
┌──────────────────┐
│  Command Handler │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
Goal Set   Inbox
    │         │
    ▼         ▼
┌────────────────────────────┐
│   Build Prompt             │
│   - PROMPT.md              │
│   - GOAL.md                │
│   - STATE.md               │
│   - INBOX.md (consume)     │
│   - Previous runs          │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│   Spawn Subagent           │
│   (sessions_spawn)         │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│   Agent Executes           │
│   - Works toward goal      │
│   - Updates STATE.md       │
│   - Signals DONE if done   │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│   Save Run Output          │
│   memory/runs/<ts>/        │
└────────────┬───────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
DONE/MAX        Continue Loop
    │                 │
    ▼                 ▼
  Stop            Next Iteration
```

## Key Differences from Arbos

| Feature | Arbos | Ralph Loop (OpenClaw) |
|---------|-------|----------------------|
| Process Manager | pm2 | OpenClaw session |
| Loop Driver | while True + threads | Heartbeat / cron |
| Trigger | Telegram `/goal` | OpenClaw message |
| Agent | Claude Code CLI | `sessions_spawn` |
| Storage | `context/` | `memory/` |
| Credentials | Encrypted .env | OpenClaw secrets |
| Notifications | Telegram | OpenClaw channel |

## Success Criteria

The skill is complete when:
1. User can set a goal with `/ralph start <goal>` and loop executes
2. Each iteration builds on previous (via STATE.md)
3. Agent can signal completion (DONE)
4. Run history is preserved
5. Failure handling with backoff works

## Future Enhancements (Out of Scope)

- Voice input/output
- Multi-agent collaboration
- Cost tracking per iteration
- Web dashboard
- Automatic goal refinement