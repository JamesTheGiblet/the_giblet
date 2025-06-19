# tests/test_phase_deliverables.py
import pytest
from pathlib import Path

# Define the project root relative to the test file
PROJECT_ROOT = Path(__file__).resolve().parent.parent

class TestPhase0Deliverables:
    """
    Tests related to the deliverables and review tasks of Phase 0.
    """

    def test_readme_exists_and_has_key_sections_for_review(self):
        """
        Tests if README.md exists, is not empty, and contains key sections
        that are prerequisites for 'Task 0.3: Review the initial vision'.
        """
        readme_file = PROJECT_ROOT / "README.md"
        assert readme_file.exists(), "README.md should exist for Phase 0 review."
        assert readme_file.stat().st_size > 0, "README.md should not be empty for Phase 0 review."
        
        content = readme_file.read_text(encoding="utf-8")
        assert "Vision & Core Philosophy" in content, "README.md should contain 'Vision & Core Philosophy' section."
        assert "Roles & Capabilities" in content, "README.md should contain 'Roles & Capabilities' section."
        assert "Suggested Architecture" in content, "README.md should contain 'Suggested Architecture' section."

    def test_roadmap_exists_and_has_key_sections_for_review(self):
        """
        Tests if roadmap.md exists, is not empty, and contains key sections
        that are prerequisites for 'Task 0.3: Review the roadmap structure'.
        """
        roadmap_file = PROJECT_ROOT / "roadmap.md"
        assert roadmap_file.exists(), "roadmap.md should exist for Phase 0 review."
        assert roadmap_file.stat().st_size > 0, "roadmap.md should not be empty for Phase 0 review."

        content = roadmap_file.read_text(encoding="utf-8")
        assert "Phase 0:" in content, "roadmap.md should reference 'Phase 0:'."
        assert "Phase 1:" in content, "roadmap.md should reference 'Phase 1:' to show planning."

    def test_task_0_3_is_documented_in_roadmap(self):
        """
        Confirms that 'Task 0.3: Reflect and Evaluate Phase Outcomes' itself is documented in roadmap.md.
        """
        roadmap_file = PROJECT_ROOT / "roadmap.md"
        assert roadmap_file.exists(), "roadmap.md should exist."
        content = roadmap_file.read_text(encoding="utf-8")
        assert "Task 0.3: Reflect and Evaluate Phase Outcomes" in content, "Task 0.3 should be documented in roadmap.md"