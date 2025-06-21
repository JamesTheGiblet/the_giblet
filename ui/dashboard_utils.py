import difflib

def format_code_diff(original_code: str, refactored_code: str, fromfile: str = "original.py", tofile: str = "refactored.py") -> str:
    """
    Generates a unified diff string between two code snippets.

    Args:
        original_code (str): The original code string.
        refactored_code (str): The refactored code string.
        fromfile (str): Label for the original file in the diff header.
        tofile (str): Label for the refactored file in the diff header.

    Returns:
        str: The unified diff string.
    """
    original_lines = original_code.splitlines(keepends=True)
    refactored_lines = refactored_code.splitlines(keepends=True)
    diff = difflib.unified_diff(original_lines, refactored_lines, fromfile=fromfile, tofile=tofile, lineterm="")
    return "".join(diff)