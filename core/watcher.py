# core/watcher.py
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import threading # Import threading

class FileSystemWatcher:
    def __init__(self, path, handler):
        self.path = path
        self.handler = handler
        self.observer = Observer()
        self._is_watching = False # Track if the observer thread is started

    def start_observing(self):
        """Starts the filesystem watcher's observer thread."""
        if not self._is_watching:
            self.observer.schedule(self.handler, self.path, recursive=True)
            self.observer.start()
            self._is_watching = True
            # print(f"👀 Giblet is now watching {self.path} for changes...") # Moved print to join_observing

    def join_observing(self):
        """Joins the observer thread (blocks the current thread)."""
        if self._is_watching:
            print(f"👀 Giblet is now watching {self.path} for changes...")
            print("   (Press Ctrl+C to stop watching)")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop_observing()
            self.observer.join()
            print("\n👀 Watch mode stopped.")

    def stop_observing(self):
        """Stops the filesystem watcher's observer thread."""
        if self._is_watching:
            self.observer.stop()
            self._is_watching = False
            # No join here, join_observing handles it

class PythonChangeEventHandler(FileSystemEventHandler): # This remains largely the same
    """Reacts to changes in Python files."""
    def on_created(self, event):
        # This event is fired when a file or directory is created.
        if not event.is_directory and event.src_path.endswith(".py"):
            print(f"\n✨ New Python file created: {event.src_path}")
            print(f"   └─ Proactive Suggestion: Consider adding this file to git or writing initial tests.")
            print("giblet> ", end="", flush=True)

    def on_modified(self, event):
        # This event is fired when a file or directory is modified.
        if not event.is_directory and event.src_path.endswith(".py"):
            print(f"\n👁️  Change detected in: {event.src_path}")
            print(f"   └─ Proactive Suggestion: Consider running tests or refactoring this file.")
            # Re-printing the prompt might be better handled by the CLI loop
            # if the watcher runs in a separate thread or context.
            # For now, we'll keep it simple.
            print("giblet> ", end="", flush=True)

def start_watching(path='.'):
    """Starts the filesystem watcher."""
    # This function is for the CLI and should block
    event_handler = PythonChangeEventHandler()
    watcher = FileSystemWatcher(path=path, handler=event_handler)
    watcher.start_observing()
    watcher.join_observing() # This will block until Ctrl+C