# tests/test_phase13_environment_integrator.py

import pytest
from pathlib import Path
import sys
import os
import time
import threading
from unittest.mock import MagicMock

# Ensure the core modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.watcher import FileSystemWatcher
from watchdog.events import FileSystemEventHandler

# --- Evaluation for Task 13.3: Filesystem Watcher ---

@pytest.fixture
def temp_watch_dir(tmp_path):
    """Creates a temporary directory to be watched during the test."""
    watch_dir = tmp_path / "watched_folder"
    watch_dir.mkdir()
    return watch_dir

def test_watcher_detects_file_creation(temp_watch_dir):
    """
    Assesses the FileSystemWatcher's ability to detect new file creations.
    """
    mock_event_handler = MagicMock(spec=FileSystemEventHandler)

    watcher = FileSystemWatcher(path=str(temp_watch_dir), handler=mock_event_handler)
    
    # FIX: Correct the method call based on the user's implementation.
    # Assuming the methods are start_observing() and stop_observing().
    # If your method is named differently (e.g., run()), please adjust.
    if hasattr(watcher, 'start_observing'):
        watcher.start_observing()
    elif hasattr(watcher, 'start'):
         watcher.start()
    else:
        pytest.fail("The watcher object does not have a 'start' or 'start_observing' method.")

    try:
        time.sleep(1)

        (temp_watch_dir / "new_test_file.py").write_text("print('hello watcher')")
        
        time.sleep(2)

        mock_event_handler.on_created.assert_called_once()
        
        call_args, _ = mock_event_handler.on_created.call_args
        event_object = call_args[0]
        assert "new_test_file.py" in event_object.src_path, "Event was for the wrong file."

    finally:
        if hasattr(watcher, 'stop_observing'):
            watcher.stop_observing()
            if hasattr(watcher, 'observer') and watcher.observer.is_alive():
                watcher.observer.join(timeout=5) # Wait for the observer thread to finish
        elif hasattr(watcher, 'stop'):
            watcher.stop()
            if hasattr(watcher, 'observer') and watcher.observer.is_alive():
                watcher.observer.join(timeout=5) # Wait for the observer thread to finish
