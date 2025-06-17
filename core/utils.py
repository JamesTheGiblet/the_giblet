# core/utils.py
import os
import subprocess
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
    """Safely reads the content of a file within the workspace."""
    try:
        path = safe_path(filepath)
        print(f"📖 Reading from {path}...")
        return path.read_text(encoding='utf-8')
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return None
    except Exception as e:
        print(f"❌ Error reading file {filepath}: {e}")
        return None

def write_file(filepath: str, content: str) -> bool:
    """Safely writes content to a file within the workspace."""
    try:
        path = safe_path(filepath)
        # Ensure the parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        print(f"✍️ Writing to {path}...")
        path.write_text(content, encoding='utf-8')
        return True
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