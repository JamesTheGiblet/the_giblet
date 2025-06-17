# api.py
from fastapi import FastAPI
import sys
from pathlib import Path

# This ensures the API can find our core modules
sys.path.append(str(Path(__file__).parent))

from core.roadmap_manager import RoadmapManager
from core.memory import Memory

# --- Initialize FastAPI and Core Modules ---
# Uvicorn looks for this specific variable named 'app'
app = FastAPI(
    title="The Giblet API",
    description="API for interacting with The Giblet's core services.",
    version="0.1.0"
)

# The API runs as a separate process and gets its own instance of the engine
memory = Memory()
roadmap_manager = RoadmapManager(memory_system=memory)


# --- API Endpoints ---
@app.get("/")
def read_root():
    """A welcome endpoint to confirm the API is running."""
    return {"message": "Welcome to The Giblet API. Navigate to /docs for details."}


@app.get("/roadmap")
def get_roadmap():
    """Returns the entire project roadmap as JSON."""
    return {"roadmap": roadmap_manager.get_tasks()}