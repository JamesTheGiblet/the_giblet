# core/roadmap_manager.py
import re
from pathlib import Path

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