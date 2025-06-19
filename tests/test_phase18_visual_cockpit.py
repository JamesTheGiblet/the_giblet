# tests/test_phase18_visual_cockpit.py

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
import json

# Ensure the api module can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from api import app
except (ImportError, ModuleNotFoundError) as e:
    pytest.fail(f"Could not import the FastAPI 'app' from api.py. Error: {e}")

client = TestClient(app)

# --- Evaluation for Task 18.1 & 18.3: Vibe-Centric UI Backends ---

def test_cockpit_focus_bar_api():
    """
    Assesses the /memory/focus endpoint that powers the dashboard's focus bar.
    - Tests setting a new focus.
    - Tests retrieving the focus.
    - Tests clearing the focus.
    """
    # 1. Set a new focus
    focus_text = "Refactoring the visual cockpit tests"
    set_response = client.post("/memory/focus", json={"focus_text": focus_text})
    assert set_response.status_code == 200
    assert set_response.json().get("current_focus") == focus_text

    # 2. Retrieve the focus to confirm it was set
    get_response = client.get("/memory/focus")
    assert get_response.status_code == 200
    assert get_response.json().get("current_focus") == focus_text

    # 3. Clear the focus
    clear_response = client.post("/memory/focus", json={"focus_text": ""}) # Empty string clears it
    assert clear_response.status_code == 200
    assert clear_response.json().get("current_focus") is None

    # 4. Retrieve again to confirm it's cleared
    get_cleared_response = client.get("/memory/focus")
    assert get_cleared_response.status_code == 200
    assert get_cleared_response.json().get("current_focus") is None

def test_cockpit_vibe_sliders_api():
    """
    Assesses the /profile/set endpoint's ability to handle updates from the 'Vibe Sliders'.
    """
    # 1. Set a new persona via the profile endpoint
    persona_payload = {
        "category": "llm_settings",
        "key": "idea_synth_persona",
        "value": "a minimalist architect"
    }
    persona_response = client.post("/profile/set", json=persona_payload)
    assert persona_response.status_code == 200, "Setting the persona should succeed."

    # 2. Set a new creativity level
    creativity_payload = {
        "category": "llm_settings",
        "key": "idea_synth_creativity",
        "value": "5" # Values from UI often come as strings
    }
    creativity_response = client.post("/profile/set", json=creativity_payload)
    assert creativity_response.status_code == 200, "Setting the creativity level should succeed."

    # 3. Retrieve the entire profile and check if the new values are present
    profile_response = client.get("/profile")
    assert profile_response.status_code == 200
    profile_data = profile_response.json().get("profile", {})
    
    llm_settings = profile_data.get("llm_settings", {})
    assert llm_settings.get("idea_synth_persona") == "a minimalist architect"
    # The UserProfile should handle converting the string "5" to an int if necessary,
    # but for this test, we check what was literally saved.
    assert llm_settings.get("idea_synth_creativity") == "5"

