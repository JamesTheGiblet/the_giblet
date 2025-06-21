#!/usr/bin/env python3
# scripts/pre-commit-hook.py

import sys
import asyncio
from pathlib import Path

# --- System Path Setup ---
# This ensures that the script can find the 'core' modules when run by Git.
# It assumes this script is in a 'scripts' directory at the project root.
project_root = Path(__file__).resolve().parent.parent
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
    print("💔 PRE-COMMIT HOOK ERROR: Could not import core modules.")
    print(f"   Error: {e}")
    print(f"   Please ensure this script is in a 'scripts/' directory and")
    print(f"   your project structure is correct.")
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
        print("✅ Sanity check passed. Proceeding with commit.")
        sys.exit(0) # Exit with 0 to allow the commit

    # --- Handle Found Discrepancies ---
    print("\n" + "="*60)
    print("⚠️  Sanity Check Warning!")
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
