# skills/create_project_structure_skill.py
from core.skill_manager import Skill
from core import utils # For file operations
from pathlib import Path

class CreateProjectStructureSkill(Skill):
    NAME = "CreateProjectDirs"
    DESCRIPTION = "Creates a standard project directory structure (e.g., src, tests, docs)."

    def can_handle(self, goal_description: str, context: dict) -> bool:
        return "create project structure" in goal_description.lower() or \
               "initialize project directories" in goal_description.lower()

    def get_parameters_needed(self) -> list[dict]:
        return [
            {"name": "base_path", "description": "The base path for the project (default: current dir).", "type": "str", "required": False},
            {"name": "dirs_to_create", "description": "Comma-separated list of directories (e.g., src,tests,docs).", "type": "str", "required": False}
        ]

    def execute(self, goal_description: str, context: dict, **params) -> bool:
        base_path_str = params.get("base_path", ".")
        dirs_str = params.get("dirs_to_create", "src,tests,docs,data")
        
        try:
            base_path = utils.safe_path(base_path_str) # Use safe_path for security
            if not base_path.exists():
                base_path.mkdir(parents=True, exist_ok=True)
            elif not base_path.is_dir():
                print(f"❌ {self.NAME}: Base path '{base_path_str}' exists but is not a directory.")
                return False

            directories_to_create = [d.strip() for d in dirs_str.split(',')]

            print(f"🛠️ {self.NAME}: Creating project structure in '{base_path}':")
            for dir_name in directories_to_create:
                dir_path = base_path / dir_name
                dir_path.mkdir(exist_ok=True)
                print(f"   ✅ Created directory: {dir_path}")
            
            print(f"🎉 {self.NAME}: Project structure created successfully.")
            return True
        except Exception as e:
            print(f"❌ {self.NAME}: Error creating project structure: {e}")
            return False