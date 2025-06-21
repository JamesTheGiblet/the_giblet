# tests/test_phase11_collaboration.py

import pytest
import sys
from pathlib import Path
import os
import uuid

# Ensure the core modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Skip all tests in this file if redis is not installed
redis = pytest.importorskip("redis")

from core.memory import Memory
from core.roadmap_manager import RoadmapManager
from core.style_preference import StylePreferenceManager

# --- Fixture for a Redis-connected Memory instance ---

@pytest.fixture
def redis_memory(monkeypatch):
    """
    Provides a Memory instance configured to use Redis and cleans up afterwards.
    Skips the test if Redis is unavailable.
    """
    # Force the backend to redis for this test
    monkeypatch.setenv("GIBLET_MEMORY_BACKEND", "redis")
    
    redis_url = os.getenv("GIBLET_REDIS_URL", "redis://localhost:6379")
    try:
        # Check for a live Redis server
        r = redis.from_url(redis_url)
        r.ping()
    except redis.exceptions.ConnectionError:
        pytest.skip("Redis server not available on GIBLET_REDIS_URL")

    # Use a unique key for the test to avoid collisions
    test_key_suffix = str(uuid.uuid4())
    memory_instance = Memory()
    
    # Override default keys for test isolation
    memory_instance.long_term_memory_key = f"giblet:test_ltm:{test_key_suffix}"
    shared_tasks_key = f"giblet:test_shared_tasks:{test_key_suffix}"
    checkpoints_key = f"giblet:test_checkpoints:{test_key_suffix}"
    
    # We need to inform the RoadmapManager about this test-specific key
    # This is a bit of a hack; a better design might inject the key.
    # For now, we'll patch the instance directly.
    monkeypatch.setattr(RoadmapManager, 'SHARED_TASKS_KEY', shared_tasks_key)
    monkeypatch.setattr(Memory, 'CHECKPOINTS_KEY', checkpoints_key)


    yield memory_instance
    
    # Teardown: clean up keys from Redis
    r.delete(memory_instance.long_term_memory_key)
    r.delete(shared_tasks_key)
    r.delete(checkpoints_key)


# --- Evaluation for Task 11.1, 11.2, 11.3: Collaboration Features ---

@pytest.mark.redis
def test_shared_todo_list(redis_memory):
    """
    Assesses the reliability of adding and viewing shared tasks via Redis.
    """
    # RoadmapManager needs a StylePreferenceManager, we can use a dummy one
    style_manager = StylePreferenceManager()
    roadmap_manager = RoadmapManager(
        memory_system=redis_memory,
        style_preference_manager=style_manager
    )
    
    assignee = "@testuser"
    description = "A shared task for evaluation."
    
    # 1. Add a shared task
    task_id = roadmap_manager.add_shared_task(description, assignee)
    assert task_id is not None, "add_shared_task should return a task_id on success."

    # 2. View shared tasks and verify the new task is present
    tasks = roadmap_manager.view_shared_tasks()
    
    assert isinstance(tasks, list)
    assert len(tasks) == 1, "There should be exactly one shared task."
    
    retrieved_task = tasks[0]
    assert retrieved_task["id"] == task_id
    assert retrieved_task["description"] == description
    assert retrieved_task["assignee"] == assignee
    assert retrieved_task["status"] == "open"

@pytest.mark.redis
def test_shared_checkpoints(redis_memory):
    """
    Assesses the reliability of saving and loading shared checkpoints via Redis.
    """
    # 1. In the first memory instance, remember some data and save a checkpoint
    checkpoint_name = "shared_test_run"
    redis_memory.remember("shared_focus", "collaboration_test")
    success = redis_memory.save_checkpoint(checkpoint_name)
    assert success, "Saving a shared checkpoint should be successful."

    # 2. Create a new Memory instance to simulate a different user/session
    memory2 = Memory() # This will also connect to Redis
    
    # Verify the new session's memory is initially empty
    assert memory2.recall("shared_focus") != "collaboration_test"

    # 3. Load the shared checkpoint into the new session
    load_success = memory2.load_checkpoint(checkpoint_name)
    assert load_success, "Loading a shared checkpoint should be successful."
    
    # 4. Verify the data was restored correctly
    assert memory2.recall("shared_focus") == "collaboration_test", "Focus should be restored from the shared checkpoint."

