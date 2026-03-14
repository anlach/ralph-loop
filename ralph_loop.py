#!/usr/bin/env python3
"""
Ralph Loop - Self-improving agent loop for OpenClaw

Based on Arbos (https://github.com/unconst/Arbos), adapted for OpenClaw.
Manages iterative goal-driven work with state tracking.
"""

import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

# Paths - use skill's own directory
SKILL_DIR = Path(__file__).parent
MEMORY_DIR = SKILL_DIR / "memory"
RUNS_DIR = MEMORY_DIR / "runs"

# Files
GOAL_FILE = MEMORY_DIR / "GOAL.md"
STATE_FILE = MEMORY_DIR / "STATE.md"
INBOX_FILE = MEMORY_DIR / "INBOX.md"
SETTINGS_FILE = MEMORY_DIR / ".ralph_settings.json"

# Default settings
DEFAULT_SETTINGS = {
    "max_iterations": 10,
    "max_cost": None,
    "notify_channel": None,
    "model": "chutes/MiniMaxAI/MiniMax-M2.5-TEE",
    "max_retries": 3,
    "timeout": 600,
    "auto_mode": False,
    "auto_delay": 5,
}


def ensure_memory_dir():
    """Ensure memory directory exists."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)


def load_settings() -> dict:
    """Load Ralph Loop settings."""
    ensure_memory_dir()
    if SETTINGS_FILE.exists():
        try:
            return {**DEFAULT_SETTINGS, **json.loads(SETTINGS_FILE.read_text())}
        except json.JSONDecodeError:
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> None:
    """Save Ralph Loop settings."""
    ensure_memory_dir()
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2))


def load_prompt(consume_inbox: bool = False, goal_step: int = 0) -> str:
    """Build full prompt: PROMPT + GOAL + STATE + INBOX + previous results."""
    parts = []

    # PROMPT.md (from skill directory)
    prompt_file = SKILL_DIR / "PROMPT.md"
    if prompt_file.exists():
        parts.append(prompt_file.read_text().strip())

    # GOAL.md
    if GOAL_FILE.exists():
        goal_text = GOAL_FILE.read_text().strip()
        if goal_text:
            header = f"## Goal (step {goal_step})" if goal_step else "## Goal"
            parts.append(f"{header}\n\n{goal_text}")

    # STATE.md
    if STATE_FILE.exists():
        state_text = STATE_FILE.read_text().strip()
        if state_text:
            parts.append(f"## State\n\n{state_text}")

    # INBOX.md
    if INBOX_FILE.exists():
        inbox_text = INBOX_FILE.read_text().strip()
        if inbox_text:
            parts.append(f"## Inbox\n\n{inbox_text}")
            if consume_inbox:
                INBOX_FILE.write_text("")

    # Previous run results (last one only)
    if RUNS_DIR.exists():
        runs = sorted(RUNS_DIR.glob("*"), key=lambda x: x.name, reverse=True)
        if runs:
            last_run = runs[0]
            rollout = last_run / "rollout.md"
            if rollout.exists():
                last_output = rollout.read_text()[:8000]
                parts.append(f"## Previous Run Output\n\n{last_output}")

    return "\n\n".join(parts)


def make_run_dir() -> Path:
    """Create a new run directory."""
    ensure_memory_dir()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / ts
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def set_goal(goal: str) -> str:
    """Set the goal."""
    ensure_memory_dir()
    GOAL_FILE.write_text(goal)
    
    # Initialize state
    STATE_FILE.write_text("# State\n\n- Goal set, ready to begin\n")
    
    # Clear inbox
    INBOX_FILE.write_text("")
    
    # Reset iteration counter
    settings = load_settings()
    settings["current_iteration"] = 0
    save_settings(settings)
    
    return f"🎯 **Ralph Loop started!**\n\n**Goal:** {goal}\n\nRun `/ralph run` to execute iterations."


def clear_goal() -> str:
    """Clear the goal (stops the loop)."""
    if GOAL_FILE.exists():
        GOAL_FILE.write_text("")
    STATE_FILE.write_text("")
    INBOX_FILE.write_text("")
    
    settings = load_settings()
    settings["current_iteration"] = 0
    save_settings(settings)
    
    return "⏹ Ralph Loop stopped."


def get_goal() -> str:
    """Get current goal."""
    if GOAL_FILE.exists():
        return GOAL_FILE.read_text().strip()
    return ""


def get_state() -> str:
    """Get current state."""
    if STATE_FILE.exists():
        return STATE_FILE.read_text()
    return ""


def update_state(updates: str) -> None:
    """Append to state."""
    current = get_state()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    STATE_FILE.write_text(current + f"\n\n---\n**{timestamp}**\n{updates}")


def is_running() -> bool:
    """Check if a goal is set."""
    return get_goal() != ""


def get_iteration() -> int:
    """Get current iteration number."""
    settings = load_settings()
    return settings.get("current_iteration", 0)


def increment_iteration() -> int:
    """Increment and return iteration number."""
    settings = load_settings()
    settings["current_iteration"] = settings.get("current_iteration", 0) + 1
    save_settings(settings)
    return settings["current_iteration"]


def _redact_secrets(text: str) -> str:
    """Redact API keys and secrets from text."""
    patterns = [
        (r'sk-[a-zA-Z0-9_\-]{20,}', '[REDACTED]'),
        (r'sk_[a-zA-Z0-9_\-]{20,}', '[REDACTED]'),
        (r'sk-proj-[a-zA-Z0-9_\-]{20,}', '[REDACTED]'),
        (r'ghp_[a-zA-Z0-9]{20,}', '[REDACTED]'),
        (r'gho_[a-zA-Z0-9]{20,}', '[REDACTED]'),
        (r'hf_[a-zA-Z0-9]{20,}', '[REDACTED]'),
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text


def run_step(settings: dict) -> dict:
    """Run one iteration of the loop - generates prompt for subagent."""
    goal_step = increment_iteration()
    prompt = load_prompt(consume_inbox=True, goal_step=goal_step)
    run_dir = make_run_dir()
    
    # Save the prompt
    (run_dir / "prompt.md").write_text(prompt)
    
    # Placeholder output - will be replaced when user runs /ralph do
    output = "[Waiting for work to be recorded with /ralph do or /ralph continue]"
    
    # Save placeholder output
    (run_dir / "rollout.md").write_text(output)
    (run_dir / "metadata.json").write_text(json.dumps({
        "step": goal_step,
        "timestamp": datetime.now().isoformat(),
        "model": settings.get("model", DEFAULT_SETTINGS["model"]),
        "pending": True,
    }, indent=2))
    
    return {
        "success": True,
        "output": output,
        "prompt": prompt,
        "done": False,
        "iteration": goal_step,
    }


def record_result(output: str, done: bool = False) -> None:
    """Record the result of a subagent run."""
    if not RUNS_DIR.exists():
        return
    
    runs = sorted(RUNS_DIR.glob("*"), key=lambda x: x.name, reverse=True)
    if runs:
        last_run = runs[0]
        output = _redact_secrets(output)
        (last_run / "rollout.md").write_text(output)
        
        # Update metadata
        metadata = json.loads((last_run / "metadata.json").read_text())
        metadata["pending"] = False
        metadata["done"] = done
        metadata["completed_at"] = datetime.now().isoformat()
        (last_run / "metadata.json").write_text(json.dumps(metadata, indent=2))
        
        # Update state with summary
        if done:
            update_state("✅ Goal marked as complete!")


def cleanup_old_runs(max_runs: int = 50):
    """Remove old run directories."""
    if not RUNS_DIR.exists():
        return
    
    runs = sorted(RUNS_DIR.glob("*"), key=lambda x: x.name, reverse=True)
    for old in runs[max_runs:]:
        shutil.rmtree(old, ignore_errors=True)


def get_logs(count: int = 5) -> str:
    """Get recent run logs."""
    if not RUNS_DIR.exists():
        return "No runs yet."
    
    runs = sorted(RUNS_DIR.glob("*"), key=lambda x: x.name, reverse=True)[:count]
    if not runs:
        return "No runs yet."
    
    lines = ["**Recent Runs:**\n"]
    for run in runs:
        metadata_file = run / "metadata.json"
        rollout_file = run / "rollout.md"
        
        if metadata_file.exists():
            metadata = json.loads(metadata_file.read_text())
            step = metadata.get("step", "?")
            timestamp = metadata.get("timestamp", "")[:19]
            pending = "⏳" if metadata.get("pending") else "✅" if metadata.get("done") else "📝"
            
            # Get snippet of output
            snippet = ""
            if rollout_file.exists():
                content = rollout_file.read_text()[:100].replace("\n", " ")
                if content:
                    snippet = f" — {content}..."
            
            lines.append(f"{pending} **Step {step}** ({timestamp}){snippet}")
    
    return "\n".join(lines)


# CLI handler
def handle_command(command: str, args: list, message=None) -> str:
    """Handle user commands."""
    settings = load_settings()
    
    if command == "start":
        if not args:
            return "Usage: `/ralph start <goal>`"
        goal = " ".join(args)
        return set_goal(goal)
    
    elif command == "stop":
        return clear_goal()
    
    elif command == "run":
        """Generate next iteration prompt and show it."""
        if not is_running():
            return "No goal set. Use `/ralph start <goal>` first."
        
        current = get_iteration()
        if current >= settings["max_iterations"]:
            clear_goal()
            return f"Reached max iterations ({settings['max_iterations']}). Loop stopped."
        
        result = run_step(settings)
        
        # Get the latest run directory to show the path
        runs = sorted(RUNS_DIR.glob("*"), key=lambda x: x.name, reverse=True)
        latest_run = runs[0].name if runs else "unknown"
        
        response = f"**Step {result['iteration']}** 📝\n\n"
        response += f"**Goal:** {get_goal()[:100]}...\n\n"
        
        # Show prompt from file (it's already saved there)
        prompt_file = RUNS_DIR / latest_run / "prompt.md"
        if prompt_file.exists():
            prompt = prompt_file.read_text()[:1500]
            response += f"**Prompt:**\n```\n{prompt}...\n```\n\n"
        
        response += f"Prompt saved to: `memory/runs/{latest_run}/prompt.md`\n\n"
        response += "Work on the goal, then use `/ralph do <result>` or `/ralph continue <result>` to record progress."
        
        return response
    
    elif command == "spawn":
        """Generate spawn command for subagent."""
        if not is_running():
            return "No goal set. Use `/ralph start <goal>` first."
        
        current = get_iteration()
        prompt = load_prompt(goal_step=current)
        
        # Get the latest run directory
        runs = sorted(RUNS_DIR.glob("*"), key=lambda x: x.name, reverse=True)
        latest_run = runs[0].name if runs else "unknown"
        
        # Build a proper spawn command with the prompt inline
        # The prompt is quite long, so we'll create a summary + reference to prompt.md
        response = f"**Subagent Spawn for Step {current}**\n\n"
        response += f"_Goal: {get_goal()[:80]}..._\n\n"
        response += f"**Full prompt saved to:** `memory/runs/{latest_run}/prompt.md`\n\n"
        
        # Show a preview of the prompt
        prompt_preview = prompt[:600] + "..." if len(prompt) > 600 else prompt
        response += f"```\n{prompt_preview}\n```\n\n"
        
        response += "**To spawn subagent:**\n"
        response += "The main agent should read the full prompt from `memory/runs/<timestamp>/prompt.md` "
        response += "and work toward the goal.\n\n"
        response += "**When done, use:** `/ralph do <result>` - or `/ralph continue <result>` to do+next in one step"
        
        return response
    
    elif command == "do":
        """Record result from subagent/operator."""
        if not is_running():
            return "No goal set. Use `/ralph start <goal>` first."
        
        result_text = " ".join(args)
        record_result(result_text, done="DONE" in result_text.upper() or "COMPLETE" in result_text.upper())
        
        current = get_iteration()
        
        # Check for completion
        if "DONE" in result_text.upper() or "COMPLETE" in result_text.upper():
            clear_goal()
            return "🎉 **Goal completed!** Great work."
        
        if current >= settings["max_iterations"]:
            clear_goal()
            return f"Max iterations ({settings['max_iterations']}) reached. Loop stopped."
        
        return f"✅ Step {current} recorded. Run `/ralph run` for next iteration."
    
    elif command == "next":
        """Advance to next iteration after work is done."""
        if not is_running():
            return "No goal set."
        
        current = get_iteration()
        if current >= settings["max_iterations"]:
            clear_goal()
            return f"Max iterations ({settings['max_iterations']}) reached."
        
        result = run_step(settings)
        return f"**Step {result['iteration']}** ready. Use `/ralph spawn` to continue."

    elif command == "continue":
        """Combine do + next in one command for streamlined workflow."""
        if not is_running():
            return "No goal set. Use `/ralph start <goal>` first."
        
        result_text = " ".join(args)
        
        # Record the result first
        record_result(result_text, done="DONE" in result_text.upper() or "COMPLETE" in result_text.upper())
        
        current = get_iteration()
        
        # Check for completion
        if "DONE" in result_text.upper() or "COMPLETE" in result_text.upper():
            clear_goal()
            return "🎉 **Goal completed!** Great work."
        
        if current >= settings["max_iterations"]:
            clear_goal()
            return f"Max iterations ({settings['max_iterations']}) reached. Loop stopped."
        
        # Advance to next iteration automatically
        result = run_step(settings)
        return f"✅ Step {current} recorded.\n\n**Step {result['iteration']}** ready. Use `/ralph spawn` or `/ralph continue <result>` to continue."
    
    elif command == "prompt":
        """Show current prompt."""
        if not is_running():
            return "No goal set."
        
        prompt = load_prompt(goal_step=get_iteration())
        return f"**Current Prompt:**\n\n{prompt}"
    
    elif command == "status":
        """Check if running and show details."""
        if is_running():
            goal = get_goal()
            current = get_iteration()
            
            response = f"🔄 **Ralph Loop running**\n\n"
            response += f"**Goal:** {goal}\n"
            response += f"**Iteration:** {current}/{settings['max_iterations']}\n"
            
            # Show recent state
            state = get_state()
            if state and len(state) > 100:
                response += f"\n**Recent state:** {state[:200]}..."
            elif state:
                response += f"\n**State:** {state[:200]}..."
            
            # Show latest run info
            runs = sorted(RUNS_DIR.glob("*"), key=lambda x: x.name, reverse=True)
            if runs:
                latest = runs[0]
                metadata_file = latest / "metadata.json"
                rollout_file = latest / "rollout.md"
                
                if metadata_file.exists():
                    metadata = json.loads(metadata_file.read_text())
                    status_emoji = "⏳" if metadata.get("pending") else "✅" if metadata.get("done") else "📝"
                    response += f"\n\n**Latest run:** {status_emoji} Step {metadata.get('step', '?')}"
                
                if rollout_file.exists():
                    rollout = rollout_file.read_text()[:150].replace("\n", " ")
                    if rollout and rollout != "[Prompt generated - use /ralph spawn to run subagent]":
                        response += f"\n**Output:** {rollout}..."
            
            return response
        
        # Not running - show recent activity
        runs = sorted(RUNS_DIR.glob("*"), key=lambda x: x.name, reverse=True)[:3]
        if runs:
            response = "⏸️ **Ralph Loop is not running.**\n\n**Recent activity:**\n"
            for run in runs:
                metadata_file = run / "metadata.json"
                if metadata_file.exists():
                    metadata = json.loads(metadata_file.read_text())
                    step = metadata.get("step", "?")
                    done = metadata.get("done", False)
                    response += f"- Step {step}: {'✅ complete' if done else '📝 pending'}\n"
            return response
        
        return "⏸️ Ralph Loop is not running."
    
    elif command == "logs":
        count = 5
        if args and args[0].isdigit():
            count = int(args[0])
        return get_logs(count)
    
    elif command == "clear":
        """Clean up old runs."""
        cleanup_old_runs()
        return "🧹 Old runs cleaned up."
    
    elif command == "state":
        """Show current state."""
        state = get_state()
        if state:
            return f"**State:**\n\n{state}"
        return "No state yet."
    
    elif command == "config":
        return f"**Settings:**\n\n```json\n{json.dumps(settings, indent=2)}\n```"
    
    elif command == "config-set":
        if len(args) < 2:
            return "Usage: `/ralph config-set <key> <value>`"
        key = args[0]
        value = args[1]
        
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                if value.lower() in ("true", "false"):
                    value = value.lower() == "true"
        
        settings[key] = value
        save_settings(settings)
        return f"✅ Updated {key} = {value}"
    
    elif command == "help":
        return """**Ralph Commands:**
- `/ralph start <goal>` - Set goal and begin
- `/ralph run` - Generate next iteration prompt
- `/ralph spawn` - Show subagent spawn guidance  
- `/ralph do <result>` - Record work done
- `/ralph continue <result>` - Record result AND advance to next step
- `/ralph next` - Advance to next iteration
- `/ralph prompt` - Show current prompt
- `/ralph status` - Check if running (detailed)
- `/ralph logs [n]` - View recent runs
- `/ralph clear` - Clean up old runs
- `/ralph state` - Show current state
- `/ralph stop` - Halt
- `/ralph config` - Show settings
- `/ralph config-set <key> <value>` - Update setting
- `/ralph help` - Show this help"""
    
    else:
        return f"Unknown command: {command}\n\nTry `/ralph help`"


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: ralph_loop.py <command> [args...]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    args = sys.argv[2:]
    result = handle_command(cmd, args)
    print(result)