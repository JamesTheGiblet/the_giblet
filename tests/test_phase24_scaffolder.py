import pytest
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock, ANY  # ✅ Import ANY from unittest.mock
import os

# Ensure the core modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.github_client import GitHubClient
from core.project_scaffold import ProjectScaffolder
from core.readme_generator import ReadmeGenerator
from core.roadmap_generator import RoadmapGenerator
from core.style_preference import StylePreferenceManager
from core import utils  # Import utils

# --- Evaluation for Task 24.1: GitHub Client ---

@patch('httpx.Client')
def test_github_client_create_repo(MockClient):
    """
    Assesses if the GitHubClient constructs the correct API request for repo creation.
    This test does NOT make a real network request.
    """
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"html_url": "https://github.com/test/new-repo"}

    mock_client_instance = MockClient.return_value.__enter__.return_value
    mock_client_instance.post.return_value = mock_response

    client = GitHubClient(token="dummy_github_token")

    repo_name = "new-test-repo"
    description = "A test repository for evaluation."

    result = client.create_repo(repo_name, description, private=True)

    mock_client_instance.post.assert_called_once()
    call_args, call_kwargs = mock_client_instance.post.call_args

    assert "https://api.github.com/user/repos" in call_args

    payload = call_kwargs.get("json", {})
    assert payload.get("name") == repo_name
    assert payload.get("description") == description
    assert payload.get("private") is True

    headers = call_kwargs.get("headers", {})
    assert headers.get("Authorization") == "token dummy_github_token"

    assert "html_url" in result, "The result should contain the data from the mock response."

# --- Evaluation for Task 24.2: Project Scaffolder ---

@pytest.fixture
def mock_generators():
    """Provides mocked generator instances for the scaffolder."""
    mock_readme_gen = MagicMock(spec=ReadmeGenerator)
    mock_readme_gen.generate.return_value = "# Mocked README"

    mock_roadmap_gen = MagicMock(spec=RoadmapGenerator)
    mock_roadmap_gen.generate.return_value = "## Mocked Roadmap"

    return mock_readme_gen, mock_roadmap_gen

@patch('core.utils.write_file')  # Mock utils.write_file
def test_project_scaffolder_local_creation(mock_write_file, tmp_path, mock_generators):
    """
    Assesses if the ProjectScaffolder can create a local project directory structure.
    """
    mock_readme_gen, mock_roadmap_gen = mock_generators
    style_manager = MagicMock(spec=StylePreferenceManager)

    scaffolder = ProjectScaffolder(
        readme_generator=mock_readme_gen,
        roadmap_generator=mock_roadmap_gen,
        style_manager=style_manager
    )

    project_name = "my-scaffolded-project"
    project_brief = {"title": project_name}

    mock_write_file.return_value = True

    project_path = scaffolder.scaffold_local(project_name, project_brief, base_path=tmp_path)

    # 1. Verify the main project directory was created
    assert project_path is not None, "Scaffolding should return a valid path."
    assert project_path.exists(), "The main project directory should be created."
    assert project_path.name == "my_scaffolded_project", "The project directory should have a sanitized name."

    # 2. Verify subdirectories
    assert (project_path / "core").is_dir(), "'core' directory should be created."
    assert (project_path / "data").is_dir(), "'data' directory should be created."
    assert (project_path / "tests").is_dir(), "'tests' directory should be created."
    assert (project_path / "ui").is_dir(), "'ui' directory should be created."
    assert (project_path / "data" / "prompts").is_dir(), "'data/prompts' directory should be created."
    assert (project_path / "data" / "documents").is_dir(), "'data/documents' directory should be created."

    # 3. Verify calls to style_manager.write_file_with_style
    style_manager.write_file_with_style.assert_any_call(
        filepath=project_path / "README.md",
        content="# Mocked README",
        style_category="documentation",
        project_root=project_path
    )
    style_manager.write_file_with_style.assert_any_call(
        filepath=project_path / "roadmap.md",
        content="## Mocked Roadmap",
        style_category="documentation",
        project_root=project_path
    )
    style_manager.write_file_with_style.assert_any_call(
        filepath=project_path / ".gitignore",
        content=ANY,
        style_category="configuration",
        project_root=project_path
    )
    style_manager.write_file_with_style.assert_any_call(
        filepath=project_path / "main.py",
        content=ANY,
        style_category="source_code",
        project_root=project_path
    )
    style_manager.write_file_with_style.assert_any_call(
        filepath=project_path / "requirements.txt",
        content=ANY,
        style_category="configuration",
        project_root=project_path
    )

    # 4. Verify that .gitkeep files are written via utils.write_file
    gitkeep_files = [
        project_path / "data" / "prompts" / ".gitkeep",
        project_path / "data" / "documents" / ".gitkeep",
        project_path / "tests" / ".gitkeep",
        project_path / "core" / ".gitkeep",
    ]
    for fpath in gitkeep_files:
        mock_write_file.assert_any_call(fpath, "", project_root=project_path)

    # 5. Verify generators were called
    mock_readme_gen.generate.assert_called_once_with(project_brief)
    mock_roadmap_gen.generate.assert_called_once_with(project_brief)
