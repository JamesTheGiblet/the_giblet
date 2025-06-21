# The Giblet: Skill Creation Guide

This guide outlines the process and requirements for creating new skills for The Giblet. Adhering to this guide will ensure your skill integrates correctly with the `SkillManager` and the `Agent`.

## 1. Skill File Naming and Location

*   **Location:** All skill files must be placed in the `the_giblet/skills/` directory.
*   **Naming:** Use a descriptive, snake_case name for your Python file (e.g., `my_awesome_skill.py`).
*   Avoid using `__init__.py` as a skill file name.

## 2. Skill Class Definition

Each skill must be defined as a Python class that inherits from `core.skill_manager.Skill`.

```python
# skills/your_skill_name_skill.py
from core.skill_manager import Skill
# Import any other necessary core modules (e.g., core.utils, core.user_profile) or standard libraries

class YourSkillNameSkill(Skill):
    # --- Required Class Attributes ---
    NAME = "YourUniqueSkillName"  # Must be a unique string, PascalCase or similar.
    DESCRIPTION = "A concise description of what this skill does." # Must be a non-empty string.

    # --- Initialization (Inherited) ---
    # The __init__ method is inherited from the base Skill class.
    # It receives user_profile, memory, and command_manager_instance.
    # You typically do not need to override __init__ unless you have specific setup needs.
    # def __init__(self, user_profile, memory, command_manager_instance):
    #     super().__init__(user_profile, memory, command_manager_instance)
    #     # Your custom initialization here, if any

    # --- Required Method Implementations ---

    def can_handle(self, goal_description: str, context: dict) -> bool:
        """
        Determines if this skill is appropriate for the given goal.
        - goal_description: The user's high-level goal or a sub-task from the agent's plan.
        - context: A dictionary that might contain relevant information (e.g., current focus, file paths).
        Return True if the skill can handle it, False otherwise.
        This method MUST be implemented by the skill.
        """
        # Example:
        # return "specific keyword" in goal_description.lower()
        raise NotImplementedError("Skill must implement can_handle")

    def get_parameters_needed(self) -> list[dict]:
        """
        Defines the parameters this skill requires to execute.
        Return a list of dictionaries, where each dictionary describes a parameter.
        Each parameter dictionary should have:
            - "name": str (parameter name)
            - "description": str (what the parameter is for)
            - "type": str (e.g., "str", "int", "bool", "filepath")
            - "required": bool (True if the parameter is mandatory)
        If no parameters are needed, return an empty list [].
        This method can be inherited if no parameters are needed (defaults to []).
        """
        # Example:
        # return [
        #     {"name": "target_file", "description": "The file to operate on.", "type": "str", "required": True},
        #     {"name": "overwrite", "description": "Whether to overwrite if exists.", "type": "bool", "required": False}
        # ]
        return [] # Default if no parameters

    def execute(self, goal_description: str, context: dict, **params) -> bool:
        """
        The main logic of the skill.
        - goal_description: The goal this skill is addressing.
        - context: Contextual information.
        - **params: Keyword arguments corresponding to `get_parameters_needed()`.
        Return True on successful execution, False on failure.
        This method MUST be implemented by the skill.
        """
        # Example:
        # target_file = params.get("target_file")
        # if not target_file:
        #     print(f"❌ {self.NAME}: Missing required parameter 'target_file'.")
        #     return False
        # print(f"⚙️ {self.NAME}: Executing on {target_file}...")
        # Access self.user_profile, self.memory, self.command_manager as needed.
        raise NotImplementedError("Skill must implement execute")

```

## 3. Skill Validation Checklist

Before considering a skill complete, ensure it meets these criteria (checked by `SkillManager`):

-   [ ] The skill class inherits from `core.skill_manager.Skill`.
-   [ ] The skill class has a `NAME` class attribute that is a unique, non-empty string and not "AbstractSkill".
-   [ ] The skill class has a `DESCRIPTION` class attribute that is a non-empty string and not the default description.
-   [ ] The skill class implements its own `can_handle(self, goal_description: str, context: dict) -> bool` method.
-   [ ] The skill class implements its own `execute(self, goal_description: str, context: dict, **params) -> bool` method.
-   [ ] (Optional but Recommended) The `get_parameters_needed(self) -> list[dict]` method is implemented if the skill requires parameters.
-   [ ] The skill can be instantiated correctly with `(user_profile, memory, command_manager_instance)`.
-   [ ] The skill file is placed in the `skills/` directory.

## 4. Best Practices

*   **Clarity:** Make `NAME` and `DESCRIPTION` clear and concise.
*   **Idempotency:** If possible, design skills to be idempotent (running them multiple times with the same input produces the same result).
*   **Error Handling:** Implement robust error handling within the `execute` method and return `False` on failure. Print informative error messages.
*   **Parameter Validation:** Inside `execute`, validate the `params` received.
*   **Use Core Modules:** Leverage `self.user_profile`, `self.memory`, and `self.command_manager` (for running other Giblet commands) as needed.
*   **Logging:** Use `print()` for user-facing messages. Consider using the `logging` module for more detailed internal logs if the skill is complex.

By following this guide, you'll help build a robust and extensible skill system for The Giblet!