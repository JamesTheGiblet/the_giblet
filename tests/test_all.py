# tests/test_all.py
import pytest
from core import utils

def test_write_and_read_file(tmp_path):
    """
    Tests that we can write content to a file and read the same content back.
    `tmp_path` is a special pytest fixture that provides a temporary directory.
    """
    # Arrange: Define the content and the path for our test file
    # We need to monkeypatch the WORKSPACE_DIR for this test to work in a temp folder
    pytest.MonkeyPatch().setattr(utils, "WORKSPACE_DIR", tmp_path)
    test_filepath = "test_file.txt"
    test_content = "This is a test.\nHello, Giblet!"

    # Act: Write the file, then read it back
    write_success = utils.write_file(test_filepath, test_content)
    read_content = utils.read_file(test_filepath)

    # Assert: Check that everything worked as expected
    assert write_success is True, "write_file should return True on success."
    assert read_content == test_content, "The content read should match the content written."

def test_safe_path_prevents_traversal(tmp_path):
    """
    Tests that our safe_path function correctly raises an error for path traversal.
    """
    pytest.MonkeyPatch().setattr(utils, "WORKSPACE_DIR", tmp_path)
    # This path tries to escape the temporary workspace directory
    malicious_path = "../../../etc/passwd"
    
    # Assert: Check that a PermissionError is raised when trying to use this path
    with pytest.raises(PermissionError):
        utils.safe_path(malicious_path)