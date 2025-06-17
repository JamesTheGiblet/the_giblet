# core/skill_manager.py
import importlib.util
import inspect
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent / "skills"

class Skill:
    """
    Base class for all skills.
    Skills should inherit from this and implement the required methods.
    """
    NAME = "AbstractSkill"
    DESCRIPTION = "This is an abstract skill and should not be used directly."

    def __init__(self, user_profile, memory, command_manager_instance):
        self.user_profile = user_profile
        self.memory = memory
        self.command_manager = command_manager_instance # To execute Giblet commands if needed

    def can_handle(self, goal_description: str, context: dict) -> bool:
        """
        Determines if this skill can handle the given goal description and context.
        Returns True if it can, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement can_handle")

    def get_parameters_needed(self) -> list[dict]:
        """
        Returns a list of parameters the skill needs, with descriptions and types.
        Example: [{"name": "filepath", "description": "The file to process", "type": "str"}]
        """
        return []

    def execute(self, goal_description: str, context: dict, **params) -> bool:
        """
        Executes the skill.
        Returns True on success, False on failure.
        """
        raise NotImplementedError("Subclasses must implement execute")


class SkillManager:
    def __init__(self, user_profile, memory, command_manager_instance):
        self.skills = {}
        self.user_profile = user_profile
        self.memory = memory
        self.command_manager = command_manager_instance
        self._discover_skills()
        print(f"🛠️ Skill Manager initialized. Found {len(self.skills)} skills.")

    def _discover_skills(self):
        """Discovers and loads skills from the SKILLS_DIR."""
        SKILLS_DIR.mkdir(exist_ok=True) # Ensure skills directory exists
        for filepath in SKILLS_DIR.glob("*.py"):
            if filepath.name == "__init__.py":
                continue
            try:
                module_name = filepath.stem
                spec = importlib.util.spec_from_file_location(module_name, filepath)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, Skill) and obj is not Skill:
                            # Instantiate the skill, passing necessary dependencies
                            skill_instance = obj(self.user_profile, self.memory, self.command_manager)
                            if hasattr(skill_instance, 'NAME') and skill_instance.NAME not in self.skills:
                                self.skills[skill_instance.NAME] = skill_instance
                                print(f"   ✅ Loaded skill: {skill_instance.NAME} from {filepath.name}")
                            else:
                                print(f"   ⚠️ Skill name conflict or missing NAME attribute in {filepath.name}")
            except Exception as e:
                print(f"   ❌ Error loading skill from {filepath.name}: {e}")

    def get_skill(self, name: str) -> Skill | None:
        """Retrieves a loaded skill by its name."""
        return self.skills.get(name)

    def list_skills(self) -> list[dict]:
        """Lists available skills with their descriptions."""
        return [{"name": name, "description": skill.DESCRIPTION} for name, skill in self.skills.items()]

    def refresh_skills(self):
        """Clears current skills and re-discovers them."""
        self.skills = {}
        self._discover_skills()
        print(f"🛠️ Skills refreshed. Found {len(self.skills)} skills.")