# core/utils.py
from importlib.metadata import files
import os
import subprocess
import platform
import logging
import re
from pathlib import Path
from core.giblet_config import giblet_config # Import the singleton

def safe_path(filepath: str) -> Path:
    """
    Resolves a given filepath to an absolute path, ensuring it's within the configured project root.
    Prevents directory traversal attacks (e.g., '../../etc/passwd').
    """
    project_root = Path(giblet_config.get_project_root()) # Get the configured project root
    resolved_path = project_root.joinpath(filepath).resolve()

    # Check if the resolved path is within the project root
    if project_root not in resolved_path.parents and resolved_path != project_root:
        raise PermissionError(f"Attempted file access outside of the configured project root: {filepath}")
    
    return resolved_path

def read_file(filepath: str) -> str | None:
    """Reads the content of a file safely."""
    try:
        path = safe_path(filepath)
        if path.exists() and path.is_file():
            return path.read_text(encoding='utf-8')
        else:
            print(f"❌ File not found or is not a file: {filepath}")
            return None
    except Exception as e:
        print(f"❌ Error reading file {filepath}: {e}")
        return None

def write_file(filepath: str, content: str) -> bool: # Removed project_root parameter
    """Writes content to a file safely."""
    try:
        path = safe_path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return True
    except Exception as e:
        print(f"❌ Error writing to file {filepath}: {e}")
        return False

def list_files(directory: str = ".") -> list[str]:
    """Lists all files recursively in a given directory within the workspace."""
    """Lists all files recursively in a given directory within the configured project root."""
    try:
        start_path = safe_path(directory)
        print(f"🔍 Listing files in {start_path}...")
        files = [str(p.relative_to(giblet_config.get_project_root())) for p in start_path.rglob('*') if p.is_file()]
        return files
    except Exception as e:
        print(f"❌ Error listing files in {directory}: {e}")
        return []

def list_directories(directory: str = ".") -> list[str]:
    """Lists all directories recursively in a given directory within the configured project root."""
    try:
        start_path = safe_path(directory)
        print(f"🔍 Listing directories in {start_path}...")
        directories = [str(p.relative_to(giblet_config.get_project_root())) for p in start_path.rglob('*') if p.is_dir()]
        return directories
    except Exception as e:
        print(f"❌ Error listing directories in {directory}: {e}")
        return []

def execute_command(command: str) -> tuple[int, str, str]:
    """
    Executes a shell command and captures its output.
    Returns a tuple of (return_code, stdout, stderr).
    """
    """The command is executed from the configured project root."""
    print(f"⚡ Executing command: '{command}'")
    try:
        # Using shlex.split is safer for command parsing, but for simplicity:
        cwd = giblet_config.get_project_root() # Use the configured project root as the current working directory
        result = subprocess.run(
            command,
            shell=True,  # Be cautious with shell=True in production
            capture_output=True,
            text=True,
            cwd=cwd
        )
        return (result.returncode, result.stdout, result.stderr)
    except Exception as e:
        print(f"❌ Error executing command '{command}': {e}")
        return (1, "", str(e))

logger = logging.getLogger(__name__)

def sanitize_filename(name: str) -> str:
    """
    Sanitizes a string to be a valid filename.
    - Converts to lowercase.
    - Replaces spaces and underscores with hyphens.
    - Removes all other non-alphanumeric characters (except hyphens).
    - Removes leading/trailing hyphens.
    """
    # Convert to lowercase and replace spaces/underscores
    s = name.lower().replace(' ', '-').replace('_', '-')
    # Remove all invalid characters
    s = re.sub(r'[^a-z0-9-]', '', s)
    # Remove consecutive hyphens
    s = re.sub(r'--+', '-', s)
    # Remove leading/trailing hyphens
    s = s.strip('-')
    return s

def sanitize_directory_name(name: str) -> str:
    """
    Sanitizes a string to be suitable for a directory name.
    - Converts to lowercase.
    - Replaces spaces and hyphens with underscores.
    - Removes characters that are not alphanumeric or underscores.
    """
    name = name.lower()
    name = re.sub(r'[\s-]+', '_', name)  # Replace spaces and hyphens with underscores
    name = re.sub(r'[^\w_]', '', name)    # Remove non-alphanumeric characters (excluding underscore)
    name = re.sub(r'_+', '_', name)      # Replace multiple underscores with a single one
    return name.strip('_')
