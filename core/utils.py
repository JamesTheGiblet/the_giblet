# core/utils.py
import os
import subprocess
import platform
import logging
import re # Add this import
from pathlib import Path

# Define a base directory for safety. All file operations will be contained here.
WORKSPACE_DIR = Path.cwd()

def safe_path(filepath: str) -> Path:
    """
    Resolves a given filepath to an absolute path, ensuring it's within the WORKSPACE_DIR.
    Prevents directory traversal attacks (e.g., '../../etc/passwd').
    """
    # Create a Path object from the input
    resolved_path = WORKSPACE_DIR.joinpath(filepath).resolve()

    # Check if the resolved path is within the workspace directory
    if WORKSPACE_DIR not in resolved_path.parents and resolved_path != WORKSPACE_DIR:
        raise PermissionError(f"Attempted file access outside of the workspace: {filepath}")
    
    return resolved_path

def read_file(filepath: str) -> str | None:
    """Reads the content of a file safely."""
    try:
        path = safe_path(filepath)
        if path and path.exists() and path.is_file():
            return path.read_text(encoding='utf-8')
        else:
            print(f"❌ File not found or is not a file: {filepath}")
            return None
    except Exception as e:
        print(f"❌ Error reading file {filepath}: {e}")
        return None

def write_file(filepath: str, content: str) -> bool:
    """Writes content to a file safely."""
    try:
        path = safe_path(filepath)
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"❌ Error writing to file {filepath}: {e}")
        return False

def list_files(directory: str = ".") -> list[str]:
    """Lists all files recursively in a given directory within the workspace."""
    try:
        start_path = safe_path(directory)
        print(f"🔍 Listing files in {start_path}...")
        files = [str(p.relative_to(WORKSPACE_DIR)) for p in start_path.rglob('*') if p.is_file()]
        return files
    except Exception as e:
        print(f"❌ Error listing files in {directory}: {e}")
        return []

def execute_command(command: str) -> tuple[int, str, str]:
    """
    Executes a shell command and captures its output.
    Returns a tuple of (return_code, stdout, stderr).
    """
    print(f"⚡ Executing command: '{command}'")
    try:
        # Using shlex.split is safer for command parsing, but for simplicity:
        result = subprocess.run(
            command,
            shell=True,  # Be cautious with shell=True in production
            capture_output=True,
            text=True,
            cwd=WORKSPACE_DIR
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
