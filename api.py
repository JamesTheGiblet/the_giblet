# api.py
from fastapi import FastAPI
from pydantic import BaseModel # <<< NEW IMPORT
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

# --- Import Core Modules ---
from core.roadmap_manager import RoadmapManager
from core.memory import Memory
from core.code_generator import CodeGenerator # <<< NEW IMPORT
from core import utils # <<< NEW IMPORT

# --- Initialize FastAPI and Core Modules ---
app = FastAPI(
    title="The Giblet API",
    description="API for interacting with The Giblet's core services.",
    version="0.1.0"
)
memory = Memory()
roadmap_manager = RoadmapManager(memory_system=memory)
code_generator = CodeGenerator() # <<< NEW INSTANCE

# --- Define Request/Response Models ---
class GenerationRequest(BaseModel):
    prompt: str

class TestGenerationRequest(BaseModel):
    filepath: str

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to The Giblet API. Navigate to /docs for details."}

@app.get("/roadmap")
def get_roadmap():
    return {"roadmap": roadmap_manager.get_tasks()}

# <<< NEW ENDPOINTS
@app.post("/generate/function")
def generate_function_endpoint(request: GenerationRequest):
    """Generates a Python function from a description."""
    code = code_generator.generate_function(request.prompt)
    return {"generated_code": code}

@app.post("/generate/tests")
def generate_tests_endpoint(request: TestGenerationRequest):
    """Generates pytest unit tests for a given file."""
    source_code = utils.read_file(request.filepath)
    if not source_code:
        return {"error": "File not found or is empty."}

    tests = code_generator.generate_unit_tests(source_code, request.filepath)
    return {"generated_code": tests}