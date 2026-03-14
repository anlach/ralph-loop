#!/usr/bin/env python3
"""
Ralph Loop - Self-improving agent loop for OpenClaw

Based on Arbos (https://github.com/unconst/Arbos), adapted for OpenClaw.
"""

import json
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Paths - use skill's own directory, not workspace
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
    "auto_delay": 5,  # seconds between iterations
}


def ensure_memory_dir():
    """Ensure memory directory exists."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


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
    prompt_file = Path(__file__).parent / "PROMPT.md"
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

    # Previous run results (last one only to save context)
    if RUNS_DIR.exists():
        runs = sorted(RUNS_DIR.glob("*"), reverse=True)
        if runs:
            last_run = runs[0]
            rollout = last_run / "rollout.md"
            if rollout.exists():
                last_output = rollout.read_text()[:8000]  # Limit context
                parts.append(f"## Previous Run Output\n\n{last_output}")

    return "\n\n".join(parts)


def make_run_dir() -> Path:
    """Create a new run directory."""
    ensure_memory_dir()
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
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
    
    return f"Ralph Loop started!\n\n**Goal:** {goal}\n\nRun `/ralph run` to execute iterations."


def clear_goal() -> str:
    """Clear the goal (stops the loop)."""
    if GOAL_FILE.exists():
        GOAL_FILE.write_text("")
    STATE_FILE.write_text("")
    INBOX_FILE.write_text("")
    
    settings = load_settings()
    settings["current_iteration"] = 0
    save_settings(settings)
    
    return "Ralph Loop stopped."


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


def spawn_subagent(prompt: str, model: str, timeout: int) -> dict:
    """Spawn a subagent to execute the prompt using sessions_spawn.
    
    This returns the prompt that should be sent - actual spawning is done by the caller.
    """
    # Truncate prompt if too long
    max_msg_len = 50000
    if len(prompt) > max_msg_len:
        prompt = prompt[:max_msg_len] + "\n\n[truncated...]"
    
    # Return structured info for the caller to spawn
    return {
        "success": True,
        "prompt": prompt,
        "model": model,
        "timeout": timeout,
        "output": None,
        "error": None,
    }


def run_step(settings: dict) -> dict:
    """Run one iteration of the loop."""
    goal_step = increment_iteration()
    prompt = load_prompt(consume_inbox=True, goal_step=goal_step)
    run_dir = make_run_dir()
    
    # Save the prompt
    (run_dir / "prompt.md").write_text(prompt)
    
    # Run the subagent
    result = spawn_subagent(
        prompt=prompt,
        model=settings.get("model", DEFAULT_SETTINGS["model"]),
        timeout=settings.get("timeout", DEFAULT_SETTINGS["timeout"]),
    )
    
    # Redact secrets from output
    output = result.get("output", "")
    output = _redact_secrets(output)
    
    # Save output
    (run_dir / "rollout.md").write_text(output)
    (run_dir / "metadata.json").write_text(json.dumps({
        "step": goal_step,
        "timestamp": datetime.now().isoformat(),
        "model": settings.get("model", DEFAULT_SETTINGS["model"]),
        "success": result.get("success", False),
        "error": result.get("error"),
    }, indent=2))
    
    # Check for DONE signal
    done = "DONE" in output.upper() or "COMPLETE" in output.upper()
    
    return {
        **result,
        "output": output,
        "done": done,
        "iteration": goal_step,
    }


def cleanup_old_runs(max_runs: int = 50):
    """Remove old run directories, keeping most recent."""
    if not RUNS_DIR.exists():
        return
    
    runs = sorted(RUNS_DIR.glob("*"), key=lambda x: x.name, reverse=True)
    for old in runs[max_runs:]:
        import shutil
        shutil.rmtree(old, ignore_errors=True)


# CLI handler - called by skill when message matches
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
        if not is_running():
            return "No goal set. Use `/ralph start <goal>` first."
        
        # Check max iterations
        current = get_iteration()
        if current >= settings["max_iterations"]:
            clear_goal()
            return f"Reached max iterations ({settings['max_iterations']}). Loop stopped."
        
        # Run one step
        result = run_step(settings)
        
        # Build response
        status = "✅" if result.get("success") else "❌"
        response = f"**Step {result['iteration']}** {status}\n\n"
        
        if result.get("done"):
            response += "🎉 Goal completed!\n\n"
            clear_goal()
        elif result["iteration"] >= settings["max_iterations"]:
            response += "Max iterations reached.\n\n"
            clear_goal()
        
        # Add output snippet
        output = result.get("output", "")
        if output:
            snippet = output[:500] + "..." if len(output) > 500 else output
            response += f"```\n{snippet}\n```"
        
        return response
    
    elif command == "status":
        if is_running():
            goal = get_goal()[:100]
            current = get_iteration()
            return f"🔄 Ralph Loop is running.\n\n**Goal:** {goal}...\n**Iteration:** {current}/{settings['max_iterations']}"
        return "⏸️ Ralph Loop is not running."
    
    elif command == "config":
        return f"**Current Settings:**\n\n```json\n{json.dumps(settings, indent=2)}\n```"
    
    elif command == "config-set":
        if len(args) < 2:
            return "Usage: `/ralph config-set <key> <value>`"
        key = args[0]
        value = args[1]
        
        # Try to parse as number
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                pass
        
        settings[key] = value
        save_settings(settings)
        
        # If auto_frequency changed, update cron job
        if key == "auto_frequency" and settings.get("auto_mode"):
            import subprocess
            # Get cron job ID
            result = subprocess.run(
                ["openclaw", "cron", "list", "--json"],
                capture_output=True,
                text=True,
            )
            import re
            match = re.search(r'([a-f0-9-]{36})\s+ralph-loop', result.stdout)
            if match:
                cron_id = match.group(1)
                subprocess.run(
                    ["openclaw", "cron", "edit", cron_id, "--every", value],
                    capture_output=True,
                )
                return f"Updated {key} = {value}\nCron job updated to run every {value}."
            return f"Updated {key} = {value} (could not update cron)"
        
        return f"Updated {key} = {value}"
    
    elif command == "help":
        return """**Ralph Commands:**
- `/ralph start <goal>` - Set goal and begin
- `/ralph run` - Execute one iteration
- `/ralph status` - Check if running
- `/ralph stop` - Halt
- `/ralph config` - Show settings
- `/ralph config-set <key> <value>` - Update setting
- `/ralph auto on` - Enable auto-run mode
- `/ralph auto off` - Disable auto-run mode
- `/ralph help` - Show this help"""
    
    elif command == "auto":
        if not args:
            settings = load_settings()
            auto_on = settings.get("auto_mode", False)
            return f"Auto-run mode is {'ON' if auto_on else 'OFF'}"
        
        if args[0] == "on":
            # Create cron job
            import subprocess
            cron_result = subprocess.run(
                ["openclaw", "cron", "add",
                 "--name", "ralph-loop",
                 "--every", "1m",
                 "--message", "/ralph run"],
                capture_output=True,
                text=True,
            )
            
            if cron_result.returncode == 0:
                settings["auto_mode"] = True
                save_settings(settings)
                return "✅ Auto-run enabled! Cron job created (runs every minute).\n\nUse `/ralph auto off` to disable."
            else:
                return f"❌ Failed to create cron job: {cron_result.stderr}"
        
        elif args[0] == "off":
            # Remove cron job
            import subprocess
            subprocess.run(
                ["openclaw", "cron", "rm", "ralph-loop"],
                capture_output=True,
            )
            settings["auto_mode"] = False
            save_settings(settings)
            return "⏹ Auto-run disabled. Cron job removed."
    
    else:
        return f"Unknown command: {command}\n\nTry `/ralph help`"


def check_and_run_loop():
    """Check if loop should run (for heartbeat)."""
    if not is_running():
        return None
    
    settings = load_settings()
    
    # Check if auto mode is enabled
    if not settings.get("auto_mode", False):
        return None
    
    current = get_iteration()
    
    if current >= settings["max_iterations"]:
        clear_goal()
        return "Max iterations reached, loop stopped."
    
    result = run_step(settings)
    
    if result.get("done"):
        clear_goal()
        return f"Goal completed after {result['iteration']} iterations!"
    
    if current >= settings["max_iterations"]:
        clear_goal()
        return f"Max iterations ({settings['max_iterations']}) reached."
    
    return f"Step {result['iteration']} complete."


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: ralph_loop.py <command> [args...]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    args = sys.argv[2:]
    result = handle_command(cmd, args)
    print(result)