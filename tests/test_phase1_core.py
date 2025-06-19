# tests/test_phase1_core.py

import pytest
from pathlib import Path
import sys
import os

# Ensure the core modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import utils
from core.command_manager import CommandManager

# --- Evaluation for Task 1.2: Core Utility Functions ---

def test_file_read_write_list(tmp_path, monkeypatch):
    """
    Assesses the stability of file I/O operations.
    - Writes content to a new file.
    - Reads the content back to verify correctness.
    - Lists files in the directory to ensure visibility.
    """
    # Temporarily set the project's WORKSPACE to the pytest tmp_path for this test.
    # This allows the utils functions to write within the temp directory
    # without triggering the "outside of workspace" security check.
    monkeypatch.setattr(utils, 'WORKSPACE_DIR', tmp_path)

    test_dir_name = "test_subdir"
    test_file_name = "test_doc.txt"
    relative_file_path = os.path.join(test_dir_name, test_file_name)
    
    # Create the subdirectory inside the temporary workspace
    (tmp_path / test_dir_name).mkdir()
    
    test_content = "This is a stability test for core utilities."

    # 1. Test write_file (using a relative path)
    write_success = utils.write_file(relative_file_path, test_content)
    assert write_success is True, "write_file should return True on success"
    assert (tmp_path / relative_file_path).exists(), "The test file should exist after writing."

    # 2. Test read_file
    read_content = utils.read_file(relative_file_path)
    assert read_content == test_content, "The content read should match the content written."

    # 3. Test list_files
    file_list = utils.list_files(test_dir_name)
    # The utility returns paths relative to the workspace, so we just check the basename
    assert test_file_name in [os.path.basename(p) for p in file_list], "list_files should find the newly created file."

def test_execute_command():
    """
    Assesses the stability of the shell command execution utility.
    - Executes a simple 'echo' command.
    - Verifies that the command ran successfully (return code 0).
    - Checks that the output (stdout) is correct.
    """
    command_to_run = "echo Hello Giblet"
    return_code, stdout, stderr = utils.execute_command(command_to_run)

    assert return_code == 0, "Executing a simple echo command should be successful."
    assert "Hello Giblet" in stdout, "The stdout should contain the echoed string."
    assert stderr.strip() == "", "A successful echo command should not produce any stderr."


# --- Evaluation for Task 1.3 & 1.4: Core CLI Stability ---

def test_command_manager_registration_and_execution():
    """
    Assesses the stability and usability of the core command handling system.
    - Registers a new command with the CommandManager.
    - Executes the command.
    - Verifies that the correct handler function was called.
    """
    # Flag to be modified by our test handler
    handler_was_called = False

    def sample_handler(args):
        nonlocal handler_was_called
        handler_was_called = True
        assert args == ["test", "arg"], "Handler should receive the correct arguments."

    command_manager = CommandManager()
    command_manager.register(
        name="sample",
        handler=sample_handler,
        description="A sample command for stability testing."
    )

    # Check registration
    assert "sample" in command_manager.commands, "The 'sample' command should be registered."

    # Check execution
    command_manager.execute("sample", ["test", "arg"])
    assert handler_was_called, "The registered handler for the 'sample' command should have been called."

def test_command_manager_unknown_command():
    """
    Ensures the CommandManager handles unknown commands gracefully.
    """
    command_manager = CommandManager()
    # We don't need to register any commands for this test.
    
    # We expect this to print an error, but not crash.
    # We can capture stdout to verify the message if needed, but for now,
    # just ensuring it runs without error is a good stability check.
    try:
        command_manager.execute("unknown_command", [])
    except Exception as e:
        pytest.fail(f"Executing an unknown command raised an unexpected exception: {e}")
