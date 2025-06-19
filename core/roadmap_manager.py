# core/roadmap_manager.py
import re
from pathlib import Path
import uuid # <<< NEW IMPORT at the top of the file
import json # <<< NEW IMPORT at the top of the file
from datetime import datetime # Ensure datetime is imported
from .style_preference import StylePreferenceManager # Import StylePreferenceManager

DEFAULT_ROADMAP_FILE = Path(__file__).parent.parent / "roadmap.md"

class RoadmapManager:
    def __init__(self, memory_system, style_preference_manager: StylePreferenceManager, roadmap_path: Path | None = None):
        self.memory = memory_system
        self.style_prefs = style_preference_manager
        if roadmap_path is None:
            self.roadmap_file_path = DEFAULT_ROADMAP_FILE
        else:
            self.roadmap_file_path = roadmap_path

        self.tasks = self._load_and_parse_roadmap()
        print(f"🗺️ Roadmap Manager initialized. Style preferences active: {self.style_prefs is not None}")
        print(f"   Using roadmap file: {self.roadmap_file_path}")

    def _load_and_parse_roadmap(self) -> list[dict]:
        if not self.roadmap_file_path.exists():
            print(f"⚠️ Roadmap file not found at {self.roadmap_file_path}.")
            return []
        print(f"🗺️ Loading and parsing roadmap from {self.roadmap_file_path}")
        try:
            content = self.roadmap_file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"❌ Error reading roadmap file {self.roadmap_file_path}: {e}")
            return []
            
        # FIX: This regex is more flexible. It accepts '-' or '*' as list markers
        # and captures the rest of the line as the description, regardless of bolding.
        task_pattern = re.compile(r"^\s*[-*]\s*\[([ xX])\]\s*(.*)")
        tasks = []
        for line in content.splitlines():
            match = task_pattern.match(line)
            if match:
                status_char, description = match.groups()
                tasks.append({
                    "status": "complete" if status_char.lower() == 'x' else "incomplete",
                    # FIX: Strip whitespace AND then strip any leftover '*' from bolding.
                    "description": description.strip().strip('*')
                })
        return tasks

    def view_roadmap(self):
        # (view_roadmap is the same)
        if not self.tasks:
            print("No tasks found in the roadmap.")
            return

        preferred_format = self.style_prefs.get_preference("roadmap.default_format", "simple_list")
        # roadmap_tone = self.style_prefs.get_preference("roadmap.default_tone", "neutral") # Not used yet

        print(f"\n--- Project Roadmap (Format: {preferred_format}) ---")

        if preferred_format == "phase_based":
            phases: dict[str, list] = {}
            current_phase_name = "General Tasks" # Default phase for tasks before any "Phase X" header
            phases[current_phase_name] = []

            for task in self.tasks:
                # Check if the task description itself is a phase header
                if task['description'].lower().startswith("phase ") or "phase " in task['description'].lower() and ":" in task['description']:
                    current_phase_name = task['description']
                    if current_phase_name not in phases:
                        phases[current_phase_name] = []
                    # Don't add the phase header itself as a task under itself, unless it's also marked as a task
                    if not (task['description'] == current_phase_name and task['status'] == 'incomplete' and not any(sub_task['description'] == task['description'] for sub_task in phases[current_phase_name])):
                         # If it's a phase header AND a task, it might be added if it's not already the key
                         pass # Phase headers are keys, tasks go into the list
                else:
                    if current_phase_name not in phases: # Should be initialized
                        phases[current_phase_name] = []
                    phases[current_phase_name].append(task)
            
            for phase_name, phase_tasks in phases.items():
                print(f"\n## {phase_name}")
                for task_item in phase_tasks:
                    icon = "✅" if task_item["status"] == "complete" else "🚧"
                    print(f" {icon} {task_item['description']}")
        elif preferred_format == "simple_list": # Default or explicit simple_list
            for task in self.tasks:
                icon = "✅" if task["status"] == "complete" else "🚧"
                print(f" {icon} {task['description']}")
        else: # Fallback for unknown formats
            print(f"(Unsupported format: {preferred_format}. Displaying as simple list.)")
            for task in self.tasks:
                icon = "✅" if task["status"] == "complete" else "🚧"
                print(f" {icon} {task['description']}")
        print("-----------------------------------\n")
    def complete_task(self, task_description: str) -> bool:
        # (complete_task is the same)
        print(f"🗺️ Attempting to complete task: '{task_description}'...")
        try:
            lines = self.roadmap_file_path.read_text(encoding='utf-8').splitlines()
            task_found = False
            for i, line in enumerate(lines):
                if task_description in line and line.strip().startswith('* [ ]'):
                    lines[i] = line.replace('* [ ]', '* [x]', 1)
                    task_found = True
                    break
            if task_found:
                self.roadmap_file_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
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
