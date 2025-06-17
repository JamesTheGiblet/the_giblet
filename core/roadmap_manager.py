# core/roadmap_manager.py
import re
from pathlib import Path
import uuid # <<< NEW IMPORT at the top of the file
import json # <<< NEW IMPORT at the top of the file
from datetime import datetime # Ensure datetime is imported

# (The ROADMAP_FILE definition is the same)
ROADMAP_FILE = Path(__file__).parent.parent / "roadmap.md"

class RoadmapManager:
    def __init__(self, memory_system):
        # (__init__ is the same)
        self.memory = memory_system
        self.tasks = self._load_and_parse_roadmap()
        print("🗺️ Roadmap Manager initialized.")

    def _load_and_parse_roadmap(self) -> list[dict]:
        # (_load_and_parse_roadmap is the same)
        if not ROADMAP_FILE.exists():
            print("⚠️ Roadmap file not found.")
            return []
        print(f"🗺️ Loading and parsing roadmap from {ROADMAP_FILE}")
        content = ROADMAP_FILE.read_text(encoding='utf-8')
        task_pattern = re.compile(r"^\s*\*\s*\[([ xX])\]\s*\*\*(.*?)\*\*", re.MULTILINE)
        tasks = []
        for match in task_pattern.finditer(content):
            status_char, description = match.groups()
            tasks.append({
                "status": "complete" if status_char.lower() == 'x' else "incomplete",
                "description": description.strip()
            })
        return tasks

    def view_roadmap(self):
        # (view_roadmap is the same)
        if not self.tasks:
            print("No tasks found in roadmap.")
            return
        print("\n--- Project Roadmap ---")
        for task in self.tasks:
            icon = "✅" if task["status"] == "complete" else "🚧"
            print(f" {icon} {task['description']}")
        print("-----------------------\n")

    def complete_task(self, task_description: str) -> bool:
        # (complete_task is the same)
        print(f"🗺️ Attempting to complete task: '{task_description}'...")
        try:
            lines = ROADMAP_FILE.read_text(encoding='utf-8').splitlines()
            task_found = False
            for i, line in enumerate(lines):
                if task_description in line and line.strip().startswith('* [ ]'):
                    lines[i] = line.replace('* [ ]', '* [x]', 1)
                    task_found = True
                    break
            if task_found:
                ROADMAP_FILE.write_text('\n'.join(lines) + '\n', encoding='utf-8')
                print(f"✅ Task '{task_description}' marked as complete.")
                self.tasks = self._load_and_parse_roadmap()
                return True
            else:
                print(f"⚠️ Task '{task_description}' not found or already complete.")
                return False
        except Exception as e:
            print(f"❌ An error occurred while updating the roadmap: {e}")
            return False

    # <<< NEW METHOD
    def get_tasks(self) -> list[dict]:
        """Returns the current list of parsed tasks."""
        return self.tasks

    # <<< NEW METHODS for shared tasks
    def add_shared_task(self, description: str, assignee: str) -> str | None:
        """Adds a task to the shared list in Redis."""
        if not self.memory.redis_client:
            print("❌ Shared tasks require the Redis memory backend.")
            return None

        task_id = f"task:{uuid.uuid4()}"
        task_data = {
            "description": description,
            "assignee": assignee,
            "status": "open",
            "created_at": datetime.now().isoformat()
        }
        # Use a Redis Hash to store all shared tasks
        self.memory.redis_client.hset("giblet:shared_tasks", task_id, json.dumps(task_data))
        print(f"✅ Shared task added for {assignee}.")
        return task_id

    def view_shared_tasks(self) -> list[dict]:
        """Views all tasks from the shared list in Redis."""
        if not self.memory.redis_client:
            print("❌ Shared tasks require the Redis memory backend.")
            return []

        tasks_data = self.memory.redis_client.hgetall("giblet:shared_tasks")

        tasks = []
        for task_id, task_json in tasks_data.items():
            task = json.loads(task_json)
            task['id'] = task_id
            tasks.append(task)

        # Sort by creation date
        return sorted(tasks, key=lambda t: t['created_at'])