#!/usr/bin/env python
# scripts/run_pre_commit_check.py

import sys
import asyncio
from pathlib import Path

# Core local imports
from core.llm_providers import GeminiProvider
from core.user_profile import UserProfile
from core.memory import Memory
from scripts.sanity_checker import SanityChecker

def main() -> int:
    """
    Initializes and runs the SanityChecker for the pre-commit hook.

    Returns:
        0 on success, 1 on failure.
    """
    print("--- Running The Giblet's Sanity Check ---")

    try:
        # The pre-commit framework runs from the project root, so '.' is correct.
        project_root = Path('.')

        # --- Initialization ---
        # As planned, we create lightweight instances for the hook.
        # This assumes your GeminiProvider can be initialized from env variables.
        llm_provider = GeminiProvider()
        temp_memory = Memory()
        temp_user_profile = UserProfile(memory_system=temp_memory)
        
        checker = SanityChecker(
            project_root=project_root,
            llm_provider=llm_provider,
            user_profile=temp_user_profile
        )

        # --- Run the asynchronous check ---
        discrepancies = asyncio.run(checker.run_pre_commit_check())

        if not discrepancies:
            print("\n✅ Sanity check passed. Proceeding with commit.")
            return 0  # Success

        # --- Handle Found Discrepancies ---
        print("\n" + "="*60)
        print("⚠️ Sanity Check Warning!")
        print("   The following discrepancies were found:")
        print("="*60)
        
        for issue in discrepancies:
            print(f"   - {issue}")
        
        print("="*60)
        print("Commit aborted. Please review the discrepancies.")
        return 1  # Failure

    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred during the sanity check: {e}", file=sys.stderr)
        return 1 # Failure

if __name__ == "__main__":
    # This allows direct execution for testing, but the framework calls main().
    sys.exit(main())