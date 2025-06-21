#!/usr/bin/env python
# scripts/pre-commit-hook.py

import sys
import asyncio
from pathlib import Path
import os
import subprocess

def find_project_root(start_path: Path) -> Path | None:
    """Searches upward from start_path for a directory containing a .git folder."""
    path = start_path.resolve()
    while path.parent != path:
        if (path / ".git").is_dir():
            return path
        path = path.parent
    return None

# Find the project root starting from the script's directory. This is robust
# even if the hook is run from .git/hooks or any other location.
project_root = find_project_root(Path(__file__).parent)
if not project_root:
    print("[ERROR] PRE-COMMIT HOOK: Could not determine project root. Is this a git repository?")
    sys.exit(1)

# --- Virtual Environment Activation ---
# Ensure the hook runs within the project's virtual environment where all
# dependencies (like GitPython) are installed.
venv_path = None
# Check for common venv names like '.venv', 'venv', or 'env'.
for venv_name in ['.venv', 'venv', 'env']:
    potential_venv_path = project_root / venv_name
    python_exe = potential_venv_path / ('Scripts' if sys.platform == "win32" else 'bin') / ('python.exe' if sys.platform == "win32" else 'python')
    if python_exe.exists():
        venv_path = potential_venv_path
        break

if venv_path:
    venv_python_path = venv_path.joinpath('Scripts' if sys.platform == 'win32' else 'bin', 'python.exe' if sys.platform == 'win32' else 'python').resolve()
    current_python_path = Path(sys.executable).resolve()
    if venv_python_path != current_python_path:
        print(f"--- Re-running pre-commit hook with venv Python: {venv_python_path} ---")
        result = subprocess.run([str(venv_python_path), __file__] + sys.argv[1:], check=False)
        sys.exit(result.returncode)

# --- System Path Setup (for core module imports) ---
# This ensures that the script can find the 'core' modules when run by Git.
sys.path.append(str(project_root))

try:
    # --- Core Module Imports ---
    # These are the dependencies needed to instantiate the SanityChecker.
    from scripts.sanity_checker import SanityChecker
    from core.llm_providers import GeminiProvider # Using a default provider for the hook
    from core.user_profile import UserProfile
    from core.memory import Memory
except ImportError as e:
    print("="*60)
    print("[ERROR] PRE-COMMIT HOOK ERROR: Could not import core modules.") # Replaced emoji
    print(f"   Error: {e}")
    print(f"   Please ensure this script is in a 'scripts/' directory and")
    print(f"   your project structure is correct, and all dependencies are installed in the venv.")
    print("="*60)
    sys.exit(1) # Exit with an error code to block the commit

def main():
    """
    The main function for the pre-commit hook.
    Initializes the SanityChecker and runs the project alignment check.
    """
    print("--- Running The Giblet's Sanity Check ---")

    # --- Initialization ---
    # For the hook, we create lightweight, temporary instances of dependencies.
    # The user_profile could potentially be loaded from disk for more context,
    # but that adds complexity. For now, a default instance is sufficient.
    temp_memory = Memory()
    temp_user_profile = UserProfile(memory_system=temp_memory)
    
    # The hook needs an LLM provider. We'll default to Gemini, assuming
    # it can be configured via environment variables (.env file).
    # This avoids hardcoding keys in the hook.
    llm_provider = GeminiProvider()
    
    # Initialize the checker
    checker = SanityChecker(
        project_root=project_root,
        llm_provider=llm_provider,
        user_profile=temp_user_profile
    )

    # Run the asynchronous check
    discrepancies = asyncio.run(checker.run_pre_commit_check())

    if not discrepancies:
        print("[OK] Sanity check passed. Proceeding with commit.")
        sys.exit(0) # Exit with 0 to allow the commit

    # --- Handle Found Discrepancies ---
    print("\n" + "="*60)
    print("[WARNING] Sanity Check Warning!") # Replaced emoji
    print("   The following discrepancies were found between your roadmap and staged files:")
    print("="*60)
    
    for issue in discrepancies:
        print(f"  - {issue}")
    
    print("="*60)

    # Ask the user for confirmation
    try:
        confirm = input("Proceed with commit anyway? (y/n): ").lower().strip()
    except (EOFError, KeyboardInterrupt):
        # If the user cancels the input (Ctrl+D/Ctrl+C), block the commit.
        print("\nCommit cancelled by user.")
        sys.exit(1)

    if confirm == 'y':
        print("Proceeding with commit as requested.")
        sys.exit(0) # Exit with 0 to allow the commit
    else:
        print("Commit aborted by user. Please review the discrepancies.")
        sys.exit(1) # Exit with 1 to block the commit

if __name__ == "__main__":
    main()
