# tests/test_phase20_knowledge_weaver.py

import pytest
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

# Ensure the core modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.proactive_learner import ProactiveLearner
from core.project_contextualizer import ProjectContextualizer
from core.user_profile import UserProfile
from core.memory import Memory
from core.git_analyzer import GitAnalyzer

# --- Evaluation for Task 20.2: Project Contextualizer ---

def test_project_contextualizer_aggregation(monkeypatch):
    """
    Assesses if the ProjectContextualizer correctly aggregates context from its sources.
    """
    # 1. Set up mocked dependencies with predictable return values
    mock_memory = MagicMock(spec=Memory)
    mock_memory.recall.return_value = "current_test_focus"

    mock_git_analyzer_instance = MagicMock(spec=GitAnalyzer)
    # ProjectContextualizer.get_recent_changes_summary() calls git_analyzer.get_commit_log()
    mock_git_analyzer_instance.get_commit_log.return_value = [
        {"sha": "abc1234", "message": "feat(context): Added new feature", "author": "Test User", "date": "2023-01-01"}
    ]
    mock_git_analyzer_instance.get_branch_status.return_value = "On branch main"
    mock_git_analyzer_instance.repo = True # Simulate an active repo

    # 2. Patch GitAnalyzer class within the project_contextualizer module to return our mock_git_analyzer_instance
    with patch('core.project_contextualizer.GitAnalyzer', return_value=mock_git_analyzer_instance) as mock_git_analyzer_class:
        contextualizer = ProjectContextualizer(
            memory_system=mock_memory,
            project_root="."
        )
        # 3. Get the aggregated context
        full_context = contextualizer.get_full_context()

    # 4. Assert that the output contains the data from all mocked sources
    assert "Focus" in full_context, "Context should include the current focus."
    assert "current_test_focus" in full_context, "Context should contain the specific focus text from memory."
    
    assert "Recent Changes" in full_context, "Context should include recent changes."
    # The ProjectContextualizer formats the commit message like: "- sha: message"
    expected_git_summary_line = "abc1234: feat(context): Added new feature"
    assert expected_git_summary_line in full_context, f"Context should contain the formatted git summary. Expected part: '{expected_git_summary_line}'"

# --- Evaluation for Task 20.1 & 20.3: Proactive Learner ---

def test_proactive_learner_suggestion_from_feedback():
    """
    Assesses if the ProactiveLearner generates relevant suggestions from user feedback.
    """
    # 1. Set up a mocked UserProfile with a specific feedback log
    mock_user_profile = MagicMock(spec=UserProfile)
    
    # Simulate a history of negative feedback for a specific type of task
    feedback_log = [
        {"rating": 1, "comment": "The plan was too simple", "context_id": "agent_plan_generation"},
        {"rating": 1, "comment": "The plan missed key steps", "context_id": "agent_plan_generation"},
        {"rating": 1, "comment": "The plan was not detailed enough", "context_id": "agent_plan_generation"} # Added a third entry
    ]
    # ProactiveLearner calls user_profile.get_feedback_log()
    mock_user_profile.get_feedback_log.return_value = feedback_log
    # Configure get_preference to return None or specific defaults to avoid MagicMock objects in suggestions
    mock_user_profile.get_preference.side_effect = lambda category, key, default=None: {
        ("llm_settings", "ai_verbosity"): None,
        ("llm_settings", "ai_tone"): None,
        ("llm_settings", "idea_synth_persona"): None,
    }.get((category, key), default)
    
    # 2. Initialize the learner with the mocked profile
    learner = ProactiveLearner(user_profile=mock_user_profile)
    
    # 3. Generate suggestions
    suggestions = learner.generate_suggestions()
    
    # 4. Assert that the suggestions are relevant to the negative feedback
    assert isinstance(suggestions, list), "Suggestions should be returned as a list."
    assert len(suggestions) > 0, "Suggestions should be generated based on the feedback."
    
    suggestion_text = " ".join(suggestions).lower()
    assert "planning" in suggestion_text or "plan" in suggestion_text, "Suggestion should address the poor plan feedback."
