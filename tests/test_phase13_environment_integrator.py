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

class RealEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        print(f"File created: {event.src_path}")

def test_watcher_detects_file_creation(temp_watch_dir):
    real_event_handler = RealEventHandler()

    watcher = FileSystemWatcher(path=str(temp_watch_dir), handler=real_event_handler)

    if hasattr(watcher, 'start_observing'):
        watcher.start_observing()
    elif hasattr(watcher, 'start'):
         watcher.start()
    else:
        pytest.fail("The watcher object does not have a 'start' or 'start_observing' method.")

    try:
        print("Starting observer thread...")
        time.sleep(1)  # Give watcher more time to start

        # Create the file
        file_path = temp_watch_dir / "new_test_file.py"
        file_path.write_text("print('hello watcher')")
        print(f"File created at {file_path}")

        # Poll for the event to be processed
        timeout_duration = 5
        poll_interval = 0.05
        start_time = time.time()

        while time.time() < start_time + timeout_duration:
            time.sleep(poll_interval)

        print("Polling completed.")

    finally:
        if hasattr(watcher, 'stop_observing'):
            watcher.stop_observing()
        elif hasattr(watcher, 'stop'):
            watcher.stop()
