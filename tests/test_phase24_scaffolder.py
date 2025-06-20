# tests/test_phase24_scaffolder.py

import pytest
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock
import os

# Ensure the core modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.github_client import GitHubClient
from core.project_scaffold import ProjectScaffolder

# --- Evaluation for Task 24.1: GitHub Client ---

@patch('httpx.Client')
def test_github_client_create_repo(MockClient):
    """
    Assesses if the GitHubClient constructs the correct API request for repo creation.
    This test does NOT make a real network request.
    """
    # 1. Setup mocks
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"html_url": "https://github.com/test/new-repo"}
    
    mock_post = MagicMock(return_value=mock_response)
    mock_client_instance = MockClient.return_value.__enter__.return_value
    mock_client_instance.post = mock_post

    # 2. Initialize the client with a dummy token
    client = GitHubClient(token="dummy_github_token")
    
    repo_name = "new-test-repo"
    description = "A test repository for evaluation."
    
    # 3. Call the method
    result = client.create_repo(repo_name, description, private=True)

    # 4. Assert that the httpx post method was called correctly
    mock_post.assert_called_once()
    call_args, call_kwargs = mock_post.call_args
    
    # Check the endpoint URL
    assert "https://api.github.com/user/repos" in call_args

    # Check the payload sent to the API
    payload = call_kwargs.get("json", {})
    assert payload.get("name") == repo_name
    assert payload.get("description") == description
    assert payload.get("private") is True
    
    # Check the headers
    headers = call_kwargs.get("headers", {})
    assert headers.get("Authorization") == "token dummy_github_token"

    assert "html_url" in result, "The result should contain the data from the mock response."

# --- Evaluation for Task 24.2: Project Scaffolder ---

def test_project_scaffolder_local_creation(tmp_path):
    """
    Assesses if the ProjectScaffolder can create a local project directory structure.
    """
    scaffolder = ProjectScaffolder()
    
    project_name = "my-scaffolded-project"
    base_path = tmp_path
    
    # The scaffolder will create the project inside the base_path
    project_path = scaffolder.scaffold_local(project_name, base_path)
    
    # 1. Verify the main project directory was created
    assert project_path.exists(), "The main project directory should be created."
    assert project_path.name == project_name, "The project directory should have the correct name."
    
    # 2. Verify subdirectories
    assert (project_path / "core").is_dir(), "'core' directory should be created."
    assert (project_path / "data").is_dir(), "'data' directory should be created."
    assert (project_path / "tests").is_dir(), "'tests' directory should be created."
    
    # 3. Verify key files
    assert (project_path / ".gitignore").is_file(), ".gitignore should be created."
    assert (project_path / "README.md").is_file(), "README.md should be created."
    assert (project_path / "main.py").is_file(), "main.py should be created."

    # 4. Check content of a file to ensure it's not empty
    readme_content = (project_path / "README.md").read_text()
    assert f"# {project_name}" in readme_content, "README should contain the project title."

