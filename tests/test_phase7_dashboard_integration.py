# tests/test_phase7_dashboard_integration.py

import pytest
import httpx
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Ensure the api module can be imported
# This assumes your main API file is named api.py in the root directory
try:
    from api import app 
except (ImportError, ModuleNotFoundError):
    # If api.py is not in the root, adjust the path as needed
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    try:
        from api import app
    except (ImportError, ModuleNotFoundError) as e:
        # Provide a helpful error message if the API file can't be found
        pytest.fail(f"Could not import the FastAPI 'app' from api.py. Please ensure the file exists and is in the project root. Error: {e}")


# Use FastAPI's TestClient for synchronous testing
client = TestClient(app)

# --- Evaluation for Task 7.1 & 7.2: Dashboard Backend Integration ---

def test_api_is_running_and_responsive():
    """
    Assesses the basic health of the FastAPI server.
    - Checks that the root endpoint returns a successful status code.
    - Verifies the welcome message is present.
    """
    try:
        response = client.get("/")
        assert response.status_code == 200, "The API root should return a 200 OK status."
        
        data = response.json()
        assert "message" in data, "The root response should contain a 'message' key."
        assert "Welcome to The Giblet API" in data["message"], "The welcome message is incorrect."

    except Exception as e:
        pytest.fail(f"The API is not running or is unresponsive. Start it with 'uvicorn api:app --reload'. Error: {e}")

def test_dashboard_roadmap_endpoint():
    """
    Assesses the stability of the /roadmap endpoint that the dashboard relies on.
    - Verifies that the endpoint is reachable and returns a success code.
    - Checks that the response contains a 'roadmap' key with a list of tasks.
    """
    try:
        response = client.get("/roadmap")
        assert response.status_code == 200, "The /roadmap endpoint should be accessible."

        data = response.json()
        assert "roadmap" in data, "The response JSON must have a 'roadmap' key."
        
        roadmap_tasks = data["roadmap"]
        assert isinstance(roadmap_tasks, list), "The 'roadmap' key should contain a list."
        
        # Check that the parsed tasks have the expected structure
        if roadmap_tasks:
            first_task = roadmap_tasks[0]
            assert "description" in first_task
            assert "status" in first_task

    except Exception as e:
        pytest.fail(f"The /roadmap endpoint failed, which would break the dashboard. Error: {e}")

