# core/watcher.py
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class PythonChangeEventHandler(FileSystemEventHandler):
    """Reacts to changes in Python files."""
    def on_modified(self, event):
        # This event is fired when a file or directory is modified.
        if not event.is_directory and event.src_path.endswith(".py"):
            print(f"\n👁️  Change detected in: {event.src_path}")
            print(f"   └─ Proactive Suggestion: Consider running tests or refactoring this file.")
            print("giblet> ", end="", flush=True) # Re-print the prompt

def start_watching(path='.'):
    """Starts the filesystem watcher."""
    event_handler = PythonChangeEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)

    print("👀 Giblet is now in watch mode, monitoring for changes in .py files...")
    print("   (Press Ctrl+C to stop watching)")

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    print("\n👀 Watch mode stopped.")