# skills/hello_world_skill.py
from core.skill_manager import Skill

class HelloWorldSkill(Skill):
    NAME = "HelloWorld"
    DESCRIPTION = "A simple skill that prints a greeting."

    def can_handle(self, goal_description: str, context: dict) -> bool:
        # This skill can be triggered by a specific phrase
        return "say hello" in goal_description.lower() or \
               "greet me" in goal_description.lower()

    def get_parameters_needed(self) -> list[dict]:
        return [{"name": "name", "description": "The name to greet.", "type": "str", "required": False}]

    def execute(self, goal_description: str, context: dict, **params) -> bool:
        name_to_greet = params.get("name", self.user_profile.get_preference("general", "user_name", "World"))
        print(f"👋 Hello, {name_to_greet}! This greeting comes from the HelloWorldSkill.")
        return True