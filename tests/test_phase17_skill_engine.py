# tests/test_phase17_skill_engine.py

import pytest
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch
import json

# Ensure the core modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import skill_manager as core_skill_manager_module # Import the module itself for monkeypatching
from core.skill_manager import SkillManager # <<< ADD THIS IMPORT
from core.command_manager import CommandManager
from core.agent import Agent
from core.idea_synth import IdeaSynthesizer
from core.code_generator import CodeGenerator
from core.llm_provider_base import LLMProvider
from core.user_profile import UserProfile
from core.memory import Memory

# --- Fixtures ---

@pytest.fixture
def dummy_skill_file(tmp_path):
    """Creates a temporary skill file in a temporary directory."""
    skills_dir = tmp_path / "test_skills"
    skills_dir.mkdir()
    
    skill_content = """
from core.skill_manager import Skill

class TestGreetSkill(Skill): # Renamed to avoid potential conflicts if a real GreetSkill exists
    NAME = "Greet"
    DESCRIPTION = "A simple skill to greet a user."

    def can_handle(self, goal_description: str, context: dict) -> bool:
        return "greet" in goal_description.lower() or "hello" in goal_description.lower()

    def get_parameters_needed(self) -> list[dict]:
        return [{"name": "name", "description": "The name of the person to greet.", "type": "str", "required": False}]

    def execute(self, goal_description: str, context: dict, **params) -> bool:
        name = params.get("name", "World")
        print(f"Hello, {name}!") # Skills typically return bool and print output
        return True
"""
    skill_file = skills_dir / "greet_skill.py"
    skill_file.write_text(skill_content)
    
    # We need to make this temporary directory importable
    sys.path.insert(0, str(skills_dir))
    yield skills_dir
    sys.path.pop(0)

@pytest.fixture
def mock_agent_for_skills():
    """Provides a mocked Agent instance for skill testing."""
    mock_llm = MagicMock(spec=LLMProvider)
    mock_llm.is_available.return_value = True
    mock_llm.model_name = "mock-model-for-skills" # Explicitly set model_name
    
    # Create real instances of IdeaSynthesizer and CodeGenerator, but inject the mock LLM
    mock_user_profile = MagicMock(spec=UserProfile)
    mock_memory = MagicMock(spec=Memory)
    mock_project_contextualizer = MagicMock()
    mock_style_preference_manager = MagicMock()

    idea_synth_instance = IdeaSynthesizer(user_profile=mock_user_profile, memory_system=mock_memory, llm_provider=mock_llm, project_contextualizer=mock_project_contextualizer, style_preference_manager=mock_style_preference_manager)
    
    code_gen_instance = CodeGenerator(user_profile=mock_user_profile, memory_system=mock_memory, llm_provider=mock_llm, project_contextualizer=mock_project_contextualizer)
    
    mock_skill_manager = MagicMock(spec=SkillManager)
    
    dependencies = {
        "idea_synth": idea_synth_instance,
        "code_generator": code_gen_instance,
        "skill_manager": mock_skill_manager
    }
    return Agent(**dependencies)

# --- Evaluation for Task 17.1, 17.2, 17.3 ---

def test_skill_manager_discovery(dummy_skill_file, monkeypatch):
    """
    Assesses if the SkillManager can discover and load a skill from a directory.
    """
    # Temporarily change the SKILLS_DIR for the SkillManager
    monkeypatch.setattr(core_skill_manager_module, 'SKILLS_DIR', dummy_skill_file)
    
    skill_manager_instance = core_skill_manager_module.SkillManager(
        user_profile=MagicMock(spec=UserProfile),
        memory=MagicMock(spec=Memory),
        command_manager_instance=MagicMock(spec=CommandManager)
    )
    
    skills = skill_manager_instance.list_skills()
    assert len(skills) == 1, "Should discover exactly one skill."
    
    skill_info = skills[0]
    assert skill_info['name'] == "Greet"
    assert "A simple skill to greet a user." in skill_info['description']

    # Clean up monkeypatch if necessary, though pytest handles fixture scope
    monkeypatch.undo()

def test_agent_skill_aware_planning(mock_agent_for_skills):
    """
    Assesses if the Agent includes discovered skills in its planning prompt.
    """
    agent = mock_agent_for_skills
    
    # Mock the skill manager to return our dummy skill
    # Agent.create_plan calls skill_manager.list_skills()
    agent.skill_manager.list_skills.return_value = [
        {"name": "Greet", "description": "A simple skill to greet a user."}
    ]
    
    # Configure the mock LLM provider to return the raw JSON string that IdeaSynthesizer expects
    mock_llm_provider = agent.idea_synth.llm_provider
    mock_llm_provider.generate_text.return_value = json.dumps(['skill Greet name="Alice"'])

    plan = agent.create_plan("say hello to Alice")
    
    # Check that the planning prompt contained the skill info
    mock_llm_provider.generate_text.assert_called_once()
    call_args, call_kwargs = mock_llm_provider.generate_text.call_args
    prompt = call_kwargs.get('prompt', call_args[0] if call_args else "")
    assert "Consider using these available skills" in prompt, "Prompt should list available skills." # Corrected assertion text
    assert "Skill Name: \"Greet\"" in prompt, "Prompt should include the Greet skill."
    
    # Check that the plan correctly uses the skill command
    assert plan[0] == 'skill Greet name="Alice"'

def test_command_manager_skill_execution(dummy_skill_file, monkeypatch, capsys):
    """
    Assesses if the CommandManager can execute a command handled by a loaded skill.
    """
    command_manager = CommandManager()
    
    # Temporarily change the SKILLS_DIR for the SkillManager
    monkeypatch.setattr(core_skill_manager_module, 'SKILLS_DIR', dummy_skill_file)

    # SkillManager's __init__ calls _discover_skills, which might try to register commands
    # if the command_manager_instance is passed and used for registration.
    # The current SkillManager doesn't auto-register, Agent/CLI does.
    # For this test, we'll manually register after skill discovery.
    skill_manager_instance = core_skill_manager_module.SkillManager(
        user_profile=MagicMock(spec=UserProfile),
        memory=MagicMock(spec=Memory),
        command_manager_instance=command_manager # Pass the real one
    )
    # Manually register the skill command for testing CommandManager execution
    greet_skill_instance = skill_manager_instance.get_skill("Greet")
    assert greet_skill_instance is not None, "Greet skill should be loaded."
    command_manager.register_skill_command(greet_skill_instance)
    
    # Execute the command
    command_manager.execute("Greet", ["name=Bob"]) # Command name is case-sensitive as per Skill.NAME
    captured = capsys.readouterr()
    assert "Hello, Bob!" in captured.out, "The skill's execute method was not called correctly or did not print."
