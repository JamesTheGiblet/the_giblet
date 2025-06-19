# tests/test_phase6_git_awareness.py

import pytest
from pathlib import Path
import sys
import os
import git
from unittest.mock import patch

# Ensure the core modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.git_analyzer import GitAnalyzer

# --- Fixture for creating a temporary Git repository ---

@pytest.fixture
def temp_repo_for_git_analyzer(tmp_path, monkeypatch):
    """
    Creates a temporary directory, initializes a Git repository, makes a commit,
    and changes the current working directory into it for the test.
    """
    repo_path = tmp_path / "test_git_repo"
    repo_path.mkdir()
    
    # Initialize a new Git repository
    repo = git.Repo.init(repo_path)
    
    # Change CWD into the new repo so that GitAnalyzer finds it
    monkeypatch.chdir(repo_path)
    
    # Create and commit a file
    (repo_path / "initial_file.txt").write_text("hello world")
    repo.index.add(["initial_file.txt"])
    repo.index.commit("Initial commit")
    
    yield repo_path

# --- Evaluation for Task 6.1, 6.2, 6.3: Git-Awareness Engine ---

def test_git_analyzer_initialization(temp_repo_for_git_analyzer):
    """
    Assesses if the GitAnalyzer initializes correctly within a git repo.
    """
    try:
        analyzer = GitAnalyzer()
        assert analyzer.repo is not None, "Analyzer should have a valid repo object."
        assert isinstance(analyzer.repo, git.Repo), "Repo object should be of type git.Repo."
    except Exception as e:
        pytest.fail(f"GitAnalyzer failed to initialize in a valid repo: {e}")

def test_git_analyzer_get_commit_log(temp_repo_for_git_analyzer):
    """
    Assesses the ability to retrieve and parse the commit log.
    """
    analyzer = GitAnalyzer()
    log = analyzer.get_commit_log(max_count=1)
    
    assert isinstance(log, list), "Commit log should be a list."
    assert len(log) == 1, "Should retrieve one commit."
    
    commit_info = log[0]
    assert "sha" in commit_info
    assert "author" in commit_info
    assert "date" in commit_info
    assert "message" in commit_info
    assert commit_info["message"] == "Initial commit"

def test_git_analyzer_get_branch_status(temp_repo_for_git_analyzer):
    """
    Assesses the ability to detect untracked files in the branch status.
    """
    # Create a new, untracked file
    (temp_repo_for_git_analyzer / "untracked_file.txt").write_text("I am not tracked.")
    
    analyzer = GitAnalyzer()
    status = analyzer.get_branch_status()
    
    # FIX: The function returns a summary string. The test should check for that summary.
    expected_message = "Uncommitted changes or untracked files present."
    assert status == expected_message, f"The status message should match the expected summary. Got: '{status}'"

def test_git_analyzer_list_branches(temp_repo_for_git_analyzer):
    """
    Assesses the ability to list all branches in the repository.
    """
    analyzer = GitAnalyzer()
    
    # The initial branch should be 'master' or 'main'
    initial_branches = analyzer.list_branches()
    assert len(initial_branches) == 1, "There should be only one branch initially."

    # Create a new branch
    analyzer.repo.create_head("dev-branch")
    
    # List again and check for the new branch
    updated_branches = analyzer.list_branches()
    assert len(updated_branches) == 2, "There should be two branches after creating one."
    
    # Branch names might have a '*' prefix if active, so we check for substrings
    branch_names_str = " ".join(updated_branches)
    assert "dev-branch" in branch_names_str, "The new branch 'dev-branch' should be in the list."

