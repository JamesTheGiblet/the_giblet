# tests/test_phase10_sentient_loop.py

import pytest
from pathlib import Path
import sys
import json # Import json
from unittest.mock import MagicMock

# Ensure the core modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.agent import Agent
from core.idea_synth import IdeaSynthesizer
from core.code_generator import CodeGenerator
from core.skill_manager import SkillManager
from core.llm_provider_base import LLMProvider

# --- Mock Fixtures for Dependencies ---

@pytest.fixture
def mock_agent_dependencies():
    """Provides a dictionary of mocked dependencies for the Agent."""
    mock_llm = MagicMock(spec=LLMProvider)
    mock_llm.is_available.return_value = True
    
    # We need to mock the IdeaSynthesizer and CodeGenerator that the Agent depends on
    mock_idea_synth = MagicMock(spec=IdeaSynthesizer)
    mock_code_gen = MagicMock(spec=CodeGenerator)
    mock_skill_manager = MagicMock(spec=SkillManager)
    
    # FIX: The Agent's __init__ accesses llm_provider on its dependencies.
    # We must add this attribute to our mocks to satisfy the Agent's constructor.
    mock_idea_synth.llm_provider = mock_llm
    mock_code_gen.llm_provider = mock_llm
    
    return {
        "idea_synth": mock_idea_synth,
        "code_generator": mock_code_gen,
        "skill_manager": mock_skill_manager
    }

# --- Evaluation for Task 10.1 & 14.1: Test-Aware Planning ---

def test_agent_creates_test_aware_plan(mock_agent_dependencies):
    """
    Assesses that the agent's planning includes test generation when appropriate.
    """
    agent = Agent(**mock_agent_dependencies)
    mock_idea_synth = mock_agent_dependencies["idea_synth"]
    
    # Mock the LLM to return a plan that includes a 'generate tests' step
    mock_idea_synth.generate_ideas.return_value = json.dumps(["generate function \"a function to add two numbers\"", "generate tests tests/test_add.py"])
    
    goal = "Create a function to add two numbers and then write tests for it"
    plan = agent.create_plan(goal)
    
    assert isinstance(plan, list)
    assert len(plan) == 2
    assert "generate tests" in plan[1], "The generated plan should include a step for generating tests."

# --- Evaluation for Task 10.3 & 14.3: Self-Correction ---

def test_agent_self_correction_prompting(mock_agent_dependencies):
    """
    Assesses that the agent's attempt_fix method creates a well-formed prompt
    containing both the buggy code and the error log for the LLM.
    """
    agent = Agent(**mock_agent_dependencies)
    
    # The agent's attempt_fix method uses the code_generator's generate_text method.
    mock_code_gen = mock_agent_dependencies["code_generator"]
    mock_code_gen.generate_text.return_value = "# a fixed version of the code"
    
    buggy_code = "def add(a, b):\n    return a - b # Incorrect logic"
    error_log = "AssertionError: assert 2 + 3 == 5, but add(2, 3) returned -1"
    
    agent.attempt_fix(buggy_code, error_log)
    
    # Verify the LLM was called to generate the fix
    mock_code_gen.generate_text.assert_called_once()
    
    # Inspect the prompt sent to the LLM
    call_args, call_kwargs = mock_code_gen.generate_text.call_args
    prompt = call_kwargs.get('prompt', call_args[0])
    
    assert buggy_code in prompt, "The prompt must contain the original buggy code."
    assert error_log in prompt, "The prompt must contain the error log from the failed test."
    assert "corrected" in prompt.lower(), "The prompt's instructions should indicate a fix is needed."
