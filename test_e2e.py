#!/usr/bin/env python3
"""
E2E tests for Ralph Loop skill.
Run with: python3 test_e2e.py
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add skill dir to path
SKILL_DIR = Path(__file__).parent
sys.path.insert(0, str(SKILL_DIR))

import ralph_loop


def test_set_and_get_goal():
    """Test setting and getting a goal."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch the memory dir
        original_memory = ralph_loop.MEMORY_DIR
        ralph_loop.MEMORY_DIR = Path(tmpdir)
        ralph_loop.RUNS_DIR = Path(tmpdir) / "runs"
        
        try:
            result = ralph_loop.set_goal("Test goal")
            assert "Ralph Loop started" in result
            assert ralph_loop.get_goal() == "Test goal"
            assert ralph_loop.is_running() == True
            print("✅ test_set_and_get_goal passed")
        finally:
            ralph_loop.MEMORY_DIR = original_memory
            ralph_loop.RUNS_DIR = original_memory / "runs"


def test_stop_goal():
    """Test stopping the loop."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_memory = ralph_loop.MEMORY_DIR
        ralph_loop.MEMORY_DIR = Path(tmpdir)
        ralph_loop.RUNS_DIR = Path(tmpdir) / "runs"
        
        try:
            ralph_loop.set_goal("Test goal")
            assert ralph_loop.is_running() == True
            
            result = ralph_loop.clear_goal()
            assert "stopped" in result.lower()
            assert ralph_loop.get_goal() == ""
            assert ralph_loop.is_running() == False
            print("✅ test_stop_goal passed")
        finally:
            ralph_loop.MEMORY_DIR = original_memory
            ralph_loop.RUNS_DIR = original_memory / "runs"


def test_run_step():
    """Test running a step."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_memory = ralph_loop.MEMORY_DIR
        original_runs = ralph_loop.RUNS_DIR
        original_lock = ralph_loop.LOCK_FILE
        
        ralph_loop.MEMORY_DIR = Path(tmpdir)
        ralph_loop.RUNS_DIR = Path(tmpdir) / "runs"
        ralph_loop.LOCK_FILE = Path(tmpdir) / ".running.lock"
        
        try:
            ralph_loop.set_goal("Test goal")
            result = ralph_loop.run_step(ralph_loop.load_settings())
            
            assert result["success"] == True
            assert result["iteration"] == 1
            assert "prompt" in result
            assert "Goal" in result["prompt"]
            print("✅ test_run_step passed")
        finally:
            ralph_loop.MEMORY_DIR = original_memory
            ralph_loop.RUNS_DIR = original_runs
            ralph_loop.LOCK_FILE = original_lock


def test_record_result():
    """Test recording result."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_memory = ralph_loop.MEMORY_DIR
        original_runs = ralph_loop.RUNS_DIR
        original_lock = ralph_loop.LOCK_FILE
        
        ralph_loop.MEMORY_DIR = Path(tmpdir)
        ralph_loop.RUNS_DIR = Path(tmpdir) / "runs"
        ralph_loop.LOCK_FILE = Path(tmpdir) / ".running.lock"
        
        try:
            ralph_loop.set_goal("Test goal")
            ralph_loop.run_step(ralph_loop.load_settings())
            
            ralph_loop.record_result("Fixed a bug", done=False)
            
            runs = list(ralph_loop.RUNS_DIR.glob("*"))
            assert len(runs) == 1
            
            output_file = runs[0] / "rollout.md"
            assert output_file.exists()
            assert "Fixed a bug" in output_file.read_text()
            print("✅ test_record_result passed")
        finally:
            ralph_loop.MEMORY_DIR = original_memory
            ralph_loop.RUNS_DIR = original_runs
            ralph_loop.LOCK_FILE = original_lock


def test_completion():
    """Test marking goal as complete."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_memory = ralph_loop.MEMORY_DIR
        ralph_loop.MEMORY_DIR = Path(tmpdir)
        ralph_loop.RUNS_DIR = Path(tmpdir) / "runs"
        
        try:
            ralph_loop.set_goal("Test goal")
            ralph_loop.run_step(ralph_loop.load_settings())
            
            result = ralph_loop.handle_command("do", ["Work", "done"])
            assert "Goal completed" in result or "completed" in result.lower()
            assert not ralph_loop.is_running()
            print("✅ test_completion passed")
        finally:
            ralph_loop.MEMORY_DIR = original_memory
            ralph_loop.RUNS_DIR = original_memory / "runs"


def test_iteration_tracking():
    """Test iteration counter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_memory = ralph_loop.MEMORY_DIR
        original_runs = ralph_loop.RUNS_DIR
        original_lock = ralph_loop.LOCK_FILE
        
        ralph_loop.MEMORY_DIR = Path(tmpdir)
        ralph_loop.RUNS_DIR = Path(tmpdir) / "runs"
        ralph_loop.LOCK_FILE = Path(tmpdir) / ".running.lock"
        
        try:
            ralph_loop.set_goal("Test goal")
            
            assert ralph_loop.get_iteration() == 0
            
            ralph_loop.run_step(ralph_loop.load_settings())
            ralph_loop.release_lock()
            assert ralph_loop.get_iteration() == 1
            
            ralph_loop.run_step(ralph_loop.load_settings())
            ralph_loop.release_lock()
            assert ralph_loop.get_iteration() == 2
            
            print("✅ test_iteration_tracking passed")
        finally:
            ralph_loop.MEMORY_DIR = original_memory
            ralph_loop.RUNS_DIR = original_runs
            ralph_loop.LOCK_FILE = original_lock


def test_state_persistence():
    """Test state file persistence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_memory = ralph_loop.MEMORY_DIR
        ralph_loop.MEMORY_DIR = Path(tmpdir)
        ralph_loop.RUNS_DIR = Path(tmpdir) / "runs"
        
        try:
            ralph_loop.set_goal("Test goal")
            ralph_loop.update_state("Tried approach A - it worked")
            
            state = ralph_loop.get_state()
            assert "approach A" in state
            assert "worked" in state
            
            print("✅ test_state_persistence passed")
        finally:
            ralph_loop.MEMORY_DIR = original_memory
            ralph_loop.RUNS_DIR = original_memory / "runs"


def test_logs():
    """Test log viewing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_memory = ralph_loop.MEMORY_DIR
        original_runs = ralph_loop.RUNS_DIR
        original_lock = ralph_loop.LOCK_FILE
        
        ralph_loop.MEMORY_DIR = Path(tmpdir)
        ralph_loop.RUNS_DIR = Path(tmpdir) / "runs"
        ralph_loop.LOCK_FILE = Path(tmpdir) / ".running.lock"
        
        try:
            ralph_loop.set_goal("Test goal")
            ralph_loop.run_step(ralph_loop.load_settings())
            ralph_loop.release_lock()
            ralph_loop.run_step(ralph_loop.load_settings())
            ralph_loop.release_lock()
            
            logs = ralph_loop.get_logs(5)
            assert "Step" in logs
            assert "Recent Runs" in logs
            
            print("✅ test_logs passed")
        finally:
            ralph_loop.MEMORY_DIR = original_memory
            ralph_loop.RUNS_DIR = original_runs
            ralph_loop.LOCK_FILE = original_lock


def test_config():
    """Test config handling."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_memory = ralph_loop.MEMORY_DIR
        original_runs = ralph_loop.RUNS_DIR
        original_settings = ralph_loop.SETTINGS_FILE
        
        ralph_loop.MEMORY_DIR = Path(tmpdir)
        ralph_loop.RUNS_DIR = Path(tmpdir) / "runs"
        ralph_loop.SETTINGS_FILE = Path(tmpdir) / ".ralph_settings.json"
        ralph_loop.ensure_memory_dir()
        
        try:
            settings = ralph_loop.load_settings()
            assert settings["max_iterations"] == 10
            
            # Update config
            result = ralph_loop.handle_command("config-set", ["max_iterations", "5"])
            assert "Updated max_iterations = 5" in result
            
            settings = ralph_loop.load_settings()
            assert settings["max_iterations"] == 5
            
            print("✅ test_config passed")
        finally:
            ralph_loop.MEMORY_DIR = original_memory
            ralph_loop.RUNS_DIR = original_runs
            ralph_loop.SETTINGS_FILE = original_settings


def test_token_control():
    """Test token control features - max_iterations stops the loop."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_memory = ralph_loop.MEMORY_DIR
        original_runs = ralph_loop.RUNS_DIR
        original_settings = ralph_loop.SETTINGS_FILE
        original_lock = ralph_loop.LOCK_FILE
        
        ralph_loop.MEMORY_DIR = Path(tmpdir)
        ralph_loop.RUNS_DIR = Path(tmpdir) / "runs"
        ralph_loop.SETTINGS_FILE = Path(tmpdir) / ".ralph_settings.json"
        ralph_loop.LOCK_FILE = Path(tmpdir) / ".running.lock"
        ralph_loop.ensure_memory_dir()
        
        try:
            # Set low max_iterations
            ralph_loop.handle_command("config-set", ["max_iterations", "2"])
            ralph_loop.set_goal("Test goal")
            
            # Run 2 iterations (at limit)
            ralph_loop.run_step(ralph_loop.load_settings())
            ralph_loop.release_lock()
            ralph_loop.run_step(ralph_loop.load_settings())
            ralph_loop.release_lock()
            
            # Should still be running (at limit, not over)
            assert ralph_loop.is_running() == True
            
            # Next run should stop (over limit)
            ralph_loop.run_step(ralph_loop.load_settings())
            assert ralph_loop.is_running() == False
            
            print("✅ test_token_control passed")
        finally:
            ralph_loop.MEMORY_DIR = original_memory
            ralph_loop.RUNS_DIR = original_runs
            ralph_loop.SETTINGS_FILE = original_settings
            ralph_loop.LOCK_FILE = original_lock


def main():
    """Run all tests."""
    print("🧪 Running Ralph Loop E2E tests...\n")
    
    tests = [
        test_set_and_get_goal,
        test_stop_goal,
        test_run_step,
        test_record_result,
        test_completion,
        test_iteration_tracking,
        test_state_persistence,
        test_logs,
        test_config,
        test_token_control,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
    
    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())