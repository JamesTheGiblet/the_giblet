# api.py
from fastapi import FastAPI
from pydantic import BaseModel # <<< NEW IMPORT
import sys
from pathlib import Path
import shlex # Add shlex if not already imported at the top of api.py


sys.path.append(str(Path(__file__).parent))

# --- Import Core Modules ---
from core.roadmap_manager import RoadmapManager
from core.memory import Memory
from core.code_generator import CodeGenerator # <<< NEW IMPORT
from core.automator import Automator # <<< NEW IMPORT
from core import utils # <<< NEW IMPORT

# --- Initialize FastAPI and Core Modules ---
app = FastAPI(
    title="The Giblet API",
    description="API for interacting with The Giblet's core services.",
    version="0.1.0"
)
memory = Memory()
roadmap_manager = RoadmapManager(memory_system=memory)
# command_manager is initialized here but has no commands registered by default.
# For the /agent/execute endpoint to work, this command_manager needs relevant commands.
automator = Automator() # <<< NEW INSTANCE
code_generator = CodeGenerator() # <<< NEW INSTANCE

# --- Define Request/Response Models ---
class GenerationRequest(BaseModel):
    prompt: str

class TestGenerationRequest(BaseModel):
    filepath: str

# 1. Add these new Pydantic models at the top with the others
class RefactorRequest(BaseModel):
    filepath: str
    instruction: str

class WriteFileRequest(BaseModel):
    filepath: str
    content: str

# 1. Add this Pydantic model with the others
class StubRequest(BaseModel):
    filepath: str

# New Pydantic models for Agent
class AgentPlanRequest(BaseModel):
    goal: str

class AgentPlanResponse(BaseModel):
    plan: list[str] | None = None
    error: str | None = None

class AgentExecuteResponse(BaseModel):
    message: str
    steps_executed: int
    tests_failed_initial: int = 0
    fix_attempts: int = 0
    self_correction_successful: bool | None = None
    final_error: str | None = None
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

# 2. Add these new endpoints at the end of the file
@app.post("/refactor")
def refactor_code_endpoint(request: RefactorRequest):
    """Reads a file, generates a refactoring, and returns both versions."""
    original_code = utils.read_file(request.filepath)
    if original_code is None:
        return {"error": f"File not found: {request.filepath}"}

    refactored_code = code_generator.refactor_code(original_code, request.instruction)

    return {
        "original_code": original_code,
        "refactored_code": refactored_code
    }

@app.post("/file/write")
def write_file_endpoint(request: WriteFileRequest):
    """Safely writes content to a file."""
    success = utils.write_file(request.filepath, request.content)
    if success:
        return {"message": "File updated successfully."}
    else:
        return {"error": "Failed to write file."}


@app.get("/files/list")
def list_files_endpoint():
    """Lists all files in the project directory recursively."""
    files = utils.list_files()
    return {"files": files}


@app.get("/file/read")
def read_file_endpoint(filepath: str):
    """Reads the content of a specific file."""
    content = utils.read_file(filepath)
    if content is None:
        return {"error": "File not found or could not be read."}
    return {"filepath": filepath, "content": content}

# 2. Add the new endpoints at the end of the file
@app.post("/automate/changelog")
def generate_changelog_endpoint():
    """Generates a changelog from the project's git history."""
    success = automator.generate_changelog()
    if success:
        return {"message": "Changelog generated successfully in data/changelogs/"}
    return {"error": "Failed to generate changelog."}


@app.post("/automate/stubs")
def generate_stubs_endpoint(request: StubRequest):
    """Adds TODO stubs to a specified Python file."""
    success = automator.generate_stubs(request.filepath)
    if success:
        return {"message": f"Stub generation complete for {request.filepath}."}
    return {"error": f"Failed to generate stubs for {request.filepath}."}


MAX_API_FIX_ATTEMPTS = 3

@app.post("/agent/plan", response_model=AgentPlanResponse)
def agent_create_plan_endpoint(request: AgentPlanRequest):
    """
    Creates a multi-step plan for the agent to achieve a goal.
    The plan is also stored in memory for potential execution.
    """
    plan = agent.create_plan(request.goal)
    if plan and not (isinstance(plan, list) and len(plan) > 0 and "Failed to generate" in plan[0]):
        memory.remember('api_last_plan', plan) # Store for API execution
        return AgentPlanResponse(plan=plan)
    elif isinstance(plan, list) and len(plan) > 0:
        return AgentPlanResponse(error=plan[0])
    else:
        return AgentPlanResponse(error="Failed to generate a plan or the plan was empty.")

@app.post("/agent/execute", response_model=AgentExecuteResponse)
def agent_execute_plan_endpoint():
    """
    Executes the most recently created plan (via /agent/plan).
    Includes self-correction logic for test failures.
    Requires command_manager to be populated with handlers for 'exec', 'write', 'generate tests', etc.
    """
    plan = memory.recall('api_last_plan')
    if not isinstance(plan, list) or not plan:
        return AgentExecuteResponse(message="Execution failed: No plan found in API memory.", steps_executed=0, final_error="No plan available. Please generate a plan first using the /agent/plan endpoint.")

    steps_executed = 0
    tests_failed_count = 0
    fix_attempts_count = 0
    correction_successful = None
    final_plan_error = None

    for i, command_string in enumerate(plan, 1):
        steps_executed += 1
        print(f"\n[API Agent Execute] --- Running Step {i}: giblet {command_string} ---")
        
        parts = shlex.split(command_string)
        if not parts:
            print(f"   └─ Skipping empty command in plan (Step {i}).")
            continue

        command_name = parts[0].lower()
        cmd_args = parts[1:]

        execution_result = command_manager.execute(command_name, cmd_args)

        return_code, stdout, stderr = 0, "", ""
        if isinstance(execution_result, tuple) and len(execution_result) == 3:
            return_code, stdout, stderr = execution_result
        
        is_test_step = (command_name == "exec" and cmd_args and "pytest" in " ".join(cmd_args))

        if is_test_step and return_code != 0:
            tests_failed_count +=1
            current_error_log = stdout + stderr
            current_return_code = return_code

            for attempt in range(MAX_API_FIX_ATTEMPTS):
                fix_attempts_count += 1
                print(f"   └─ [API] Tests failed. Attempting self-correction ({attempt + 1}/{MAX_API_FIX_ATTEMPTS})...")
                file_to_test = memory.recall('last_file_written')
                if not file_to_test and len(cmd_args) > 0:
                    for arg_path in cmd_args:
                        if Path(arg_path).is_file() and arg_path.endswith(".py"):
                            file_to_test = arg_path
                            break
                
                if file_to_test:
                    code_to_fix = utils.read_file(file_to_test)
                    if code_to_fix:
                        print(f"   └─ [API] LLM attempting to fix {file_to_test}...")
                        fixed_code = agent.attempt_fix(code_to_fix, current_error_log)
                        print(f"   └─ [API] Proposed fix by LLM for {file_to_test}:\n-------\n{fixed_code}\n-------")
                        
                        has_actual_code = any(line.strip() and not line.strip().startswith("#") for line in fixed_code.splitlines())
                        if fixed_code and has_actual_code:
                            utils.write_file(file_to_test, fixed_code)
                            print(f"   └─ [API] Applied potential fix to {file_to_test}. Retrying tests...")
                            current_return_code, retry_stdout, retry_stderr = command_manager.execute("exec", cmd_args)
                            current_error_log = retry_stdout + retry_stderr

                            if current_return_code == 0:
                                print("   └─ [API] Self-correction successful! Tests now pass.")
                                correction_successful = True
                                break 
                            else:
                                print(f"   └─ [API] Self-correction attempt {attempt + 1} failed. Tests still failing.")
                                if attempt + 1 == MAX_API_FIX_ATTEMPTS:
                                     final_plan_error = f"Max fix attempts reached for step {i}. Last error: {current_error_log}"
                        else:
                            print(f"   └─ [API] LLM did not provide a valid fix on attempt {attempt + 1}.")
                            final_plan_error = f"LLM did not provide a valid fix for step {i} on attempt {attempt + 1}."
                            break 
                    else:
                        print(f"   └─ [API] Could not read file {file_to_test} to attempt fix.")
                        final_plan_error = f"Could not read file {file_to_test} for step {i}."
                        break
                else:
                    print("   └─ [API] Could not determine which file to fix.")
                    final_plan_error = f"Could not determine file to fix for step {i}."
                    break
            if correction_successful is False: break

    message = f"Plan execution completed in {steps_executed} steps."
    if final_plan_error: message = f"Plan execution completed with errors after {steps_executed} steps."
    elif correction_successful: message = f"Plan execution completed successfully in {steps_executed} steps, with self-correction."
    
    return AgentExecuteResponse( message=message, steps_executed=steps_executed, tests_failed_initial=tests_failed_count, fix_attempts=fix_attempts_count,self_correction_successful=correction_successful,final_error=final_plan_error)