# tests/test_phase2_memory_planning.py

import pytest
from pathlib import Path
import sys
import os
import json

# Ensure the core modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.memory import Memory
from core.roadmap_manager import RoadmapManager
from core.style_preference import StylePreferenceManager # RoadmapManager depends on this

# --- Evaluation for Task 2.1 & 2.3: Memory Persistence ---

@pytest.fixture
def temp_memory_file(tmp_path):
    """Fixture to create a temporary memory.json file for isolated testing."""
    memory_file = tmp_path / "memory.json"
    # The Memory class should handle file creation, but we can touch it to be safe.
    memory_file.touch()
    return memory_file

def test_memory_session_vs_long_term_persistence(temp_memory_file):
    """
    Assesses the difference between session (temporary) and long-term (persistent) memory.
    NOTE: This test failing points to a likely bug in core/memory.py.
    The session_memory might be a class variable instead of an instance variable.
    """
    # --- First Session ---
    memory1 = Memory(file_path=temp_memory_file)
    memory1.remember("session_key", "volatile_value")
    memory1.commit("persistent_key", "stable_value")
    
    assert memory1.recall("session_key") == "volatile_value"
    assert memory1.retrieve("persistent_key") == "stable_value"

    # --- Simulate Restart by creating a new instance ---
    memory2 = Memory(file_path=temp_memory_file)

    # Verify session memory is gone and long-term memory remains
    assert memory2.recall("session_key") == "I don't have a memory for 'session_key'.", "Session memory should not persist across instances."
    assert memory2.retrieve("persistent_key") == "stable_value", "Long-term memory should be loaded from the file."

def test_memory_checkpoints(tmp_path):
    """
    Assesses the ability to save and load session checkpoints.
    """
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()
    
    memory = Memory(checkpoint_directory=checkpoint_dir)
    memory.remember("focus", "testing_checkpoints")
    memory.remember("last_file", "test.py")

    # 1. Save checkpoint
    checkpoint_name = "test_run"
    memory.save_checkpoint(checkpoint_name)
    
    # FIX: The application log shows it saves as a '.vibe' file.
    # The test should check for the correct file extension.
    expected_file = checkpoint_dir / f"{checkpoint_name}.vibe"
    assert expected_file.exists(), "A checkpoint file with a .vibe extension should have been created."

    # 2. Clear current session and load from checkpoint
    memory.session_memory = {}
    assert memory.recall("focus") == "I don't have a memory for 'focus'." # Verify it's cleared
    
    memory.load_checkpoint(checkpoint_name)

    # 3. Verify data was restored
    assert memory.recall("focus") == "testing_checkpoints", "Focus should be restored from checkpoint."
    assert memory.recall("last_file") == "test.py", "Last file should be restored from checkpoint."


# --- Evaluation for Task 2.2: Roadmap Manager Accuracy ---

@pytest.fixture
def temp_roadmap_file(tmp_path):
    """Fixture to create a temporary roadmap.md file."""
    roadmap_content = """
# Project Roadmap

## Phase 1: **Setup**
* [x] **Task 1: Complete**
* [ ] **Task 2: Incomplete**

## Phase 2: **Features**
* [ ] **Task 3: Also Incomplete**
"""
    roadmap_file = tmp_path / "roadmap.md"
    roadmap_file.write_text(roadmap_content, encoding="utf-8")
    return roadmap_file

def test_roadmap_manager_parsing(temp_roadmap_file):
    """
    Assesses the accuracy of the RoadmapManager's parsing logic.
    NOTE: This test failing points to a likely bug in core/roadmap_manager.py.
    The logic in get_tasks() is likely not parsing the file content correctly.
    """
    style_manager = StylePreferenceManager() 
    
    roadmap_manager = RoadmapManager(
        roadmap_path=temp_roadmap_file,
        memory_system=Memory(), # Dummy memory
        style_preference_manager=style_manager
    )

    tasks = roadmap_manager.get_tasks()

    assert len(tasks) == 3, "RoadmapManager should parse exactly 3 tasks."
    
    assert tasks[0]['description'] == "Task 1: Complete"
    assert tasks[0]['status'] == "complete"
    
    assert tasks[1]['description'] == "Task 2: Incomplete"
    assert tasks[1]['status'] == "incomplete"
    
    assert tasks[2]['description'] == "Task 3: Also Incomplete"
    assert tasks[2]['status'] == "incomplete"
