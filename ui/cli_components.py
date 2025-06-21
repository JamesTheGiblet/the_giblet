# ui/cli_components.py

def display_duplication_report(report: dict):
    """
    Prints a formatted report of code duplication analysis to the console.

    Args:
        report (dict): The duplication analysis report containing 'syntactic' and 'semantic' keys.
    """
    print("\n--- Code Duplication Report ---")

    # --- Print Syntactic Results ---
    syntactic_dupes = report.get('syntactic', [])
    if not syntactic_dupes:
        print("\n[OK] No STRUCTURALLY duplicate functions found.")
    else:
        print(f"\n[ALERT] Found {len(syntactic_dupes)} group(s) of STRUCTURALLY duplicate functions:")
        for i, group in enumerate(syntactic_dupes, 1):
            print(f"\n--- Structural Group {i} ---")
            for location in group:
                print(f"  - File: {location['file']}, Function: `{location['function_name']}`, Line: {location['line_number']}")

    # --- Print Semantic Results ---
    semantic_dupes = report.get('semantic', [])
    if not semantic_dupes:
        print("\n[OK] No CONCEPTUALLY similar functions found.")
    else:
        print(f"\n[ALERT] Found {len(semantic_dupes)} group(s) of CONCEPTUALLY similar functions:")
        for i, group in enumerate(semantic_dupes, 1):
            print(f"\n--- Conceptual Group {i} ---")
            for location in group:
                print(f"  - File: {location['file']}, Function: `{location['function_name']}`, Line: {location['line_number']}")
                print(f"    Docstring: \"{location['docstring']}\"")
    print("\n---------------------------------\n")