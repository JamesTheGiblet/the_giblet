# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel # <<< NEW IMPORT
import sys
from pathlib import Path # Keep Path import
import shlex # Add shlex if not already imported at the top of api.py
import json # Add this
from typing import Any # Import Any
from core.style_preference import StylePreferenceManager # Import StylePreferenceManager

sys.path.append(str(Path(__file__).parent))

# --- Import Core Modules ---
from core import user_profile
from core.idea_synth import IdeaSynthesizer
from core.roadmap_manager import RoadmapManager
from core.memory import Memory
from core.code_generator import CodeGenerator # <<< NEW IMPORT
from core.automator import Automator # <<< NEW IMPORT
from core import agent, command_manager, utils, user_profile as core_user_profile # <<< NEW IMPORT, aliased user_profile
from core.user_profile import UserProfile # New import
from core.skill_manager import SkillManager # New import
from core.llm_provider_base import LLMProvider # Import base provider
# --- Add these to your Core Module Imports ---
from core.github_client import GitHubClient
from core.project_scaffold import ProjectScaffolder
from core.readme_generator import ReadmeGenerator # Already imported, keep
from core.roadmap_generator import RoadmapGenerator # Already imported, keep
from core.llm_providers import GeminiProvider, OllamaProvider # Import specific providers
from core.project_contextualizer import ProjectContextualizer # Import ProjectContextualizer
from core.modularity_guardrails import ModularityGuardrails
from core.readme_generator import ReadmeGenerator # Add near the top with other core imports
from core.roadmap_generator import RoadmapGenerator # Add with other core imports

# --- Initialize FastAPI and Core Modules ---
app = FastAPI(
    title="The Giblet API",
    description="API for interacting with The Giblet's core services.",
    version="0.1.0"
)
memory = Memory()
style_manager_for_api = StylePreferenceManager() # Instantiate StylePreferenceManager
roadmap_manager = RoadmapManager(memory_system=memory, style_preference_manager=style_manager_for_api) # Pass it here
user_profile_instance = UserProfile(memory_system=memory) # Instantiate UserProfile, renamed to avoid conflict
# Instantiate CommandManager for the API, passing the memory system
command_manager_for_api = command_manager.CommandManager(memory_system=memory)
# command_manager is initialized here but has no commands registered by default.
# For the /agent/execute endpoint to work, this command_manager needs relevant commands.
modularity_guardrails = ModularityGuardrails()
automator = Automator() # <<< NEW INSTANCE

# Helper function to get the configured LLM provider
def get_configured_llm_provider(profile: UserProfile) -> LLMProvider | None:
    active_provider_name = profile.get_preference("llm_provider_config", "active_provider", "gemini")
    raw_provider_configs = profile.get_preference("llm_provider_config", "providers")

    provider_configs = {}
    if isinstance(raw_provider_configs, dict):
        provider_configs = raw_provider_configs
    elif isinstance(raw_provider_configs, str) and raw_provider_configs.startswith("{") and raw_provider_configs.endswith("}"): # Basic check for JSON string
        try:
            provider_configs = json.loads(raw_provider_configs) # Attempt to parse if it's a stringified JSON
        except json.JSONDecodeError:
            print(f"⚠️ API: Could not parse 'providers' config string from profile. Using defaults. String was: {raw_provider_configs}")
            provider_configs = core_user_profile.DEFAULT_PROFILE_STRUCTURE["llm_provider_config"]["providers"]
    else: # Not a dict, not a parsable string, or None
        print(f"⚠️ API: 'providers' config in profile is not a valid dictionary. Using defaults. Value was: {raw_provider_configs}")
        provider_configs = core_user_profile.DEFAULT_PROFILE_STRUCTURE["llm_provider_config"]["providers"] # Fallback to default structure

    if active_provider_name == "gemini":
        gemini_config = provider_configs.get("gemini", {})
        api_key = gemini_config.get("api_key") # GeminiProvider will use .env if this is empty/None
        model_name = gemini_config.get("model_name", "gemini-1.5-flash-latest")
        print(f"API: Configuring GeminiProvider (model: {model_name}, API key from profile: {'yes' if api_key else 'no/use .env'})")
        return GeminiProvider(model_name=model_name, api_key=api_key if api_key else None)
    elif active_provider_name == "ollama":
        ollama_config = provider_configs.get("ollama", {})
        base_url = ollama_config.get("base_url", "http://localhost:11434")
        model_name = ollama_config.get("model_name", "mistral")
        print(f"API: Configuring OllamaProvider (model: {model_name}, url: {base_url})")
        return OllamaProvider(model_name=model_name, base_url=base_url)
    else:
        print(f"⚠️ API: Unknown LLM provider '{active_provider_name}' configured in profile. Defaulting to Gemini.")
        return GeminiProvider() # Fallback

api_llm_provider = get_configured_llm_provider(user_profile_instance)

if not api_llm_provider or not api_llm_provider.is_available():
    print(f"⚠️ API: Configured LLM provider ({api_llm_provider.PROVIDER_NAME if api_llm_provider else 'N/A'}) is not available. Operations requiring LLM will be affected.")
    # Fallback to a default if primary is not available, or let it be None and handle in consuming classes
    if not (api_llm_provider and api_llm_provider.is_available()): # Double check if primary failed
        print("⚠️ API: Attempting fallback to Gemini (default) due to primary provider unavailability.")
        api_llm_provider = GeminiProvider() # Default fallback
        if not api_llm_provider.is_available():
            print("⚠️ API: Fallback Gemini provider also not available. LLM features will be severely limited.")
            api_llm_provider = None # Or a NoOpLLMProvider

# --- Add these initializations with your other core modules ---
# These generators are needed by the scaffolder
readme_generator_api = ReadmeGenerator(llm_provider=api_llm_provider, style_manager=style_manager_for_api) # Already initialized, keep
roadmap_generator_api = RoadmapGenerator(llm_provider=api_llm_provider, style_manager=style_manager_for_api) # Already initialized, keep

github_client_api = GitHubClient()
project_scaffolder_api = ProjectScaffolder(
 readme_generator=readme_generator_api,
 roadmap_generator=roadmap_generator_api,
 style_manager=style_manager_for_api
)

project_contextualizer_api = ProjectContextualizer(memory_system=memory, project_root=".")

idea_synth_for_api = IdeaSynthesizer(user_profile=user_profile_instance,
 memory_system=memory,
 llm_provider=api_llm_provider,
 project_contextualizer=project_contextualizer_api,
 style_preference_manager=style_manager_for_api) # Pass StylePreferenceManager
# Instantiate the ReadmeGenerator for the API
readme_generator_for_api = ReadmeGenerator(
    llm_provider=api_llm_provider,
    style_manager=style_manager_for_api
)
# Instantiate the RoadmapGenerator for the API
roadmap_generator_for_api = RoadmapGenerator(
    llm_provider=api_llm_provider,
    style_manager=style_manager_for_api
)

code_generator = CodeGenerator(user_profile=user_profile_instance, memory_system=memory, llm_provider=api_llm_provider, project_contextualizer=project_contextualizer_api)
skill_manager_for_api = SkillManager(user_profile=user_profile_instance, memory=memory, command_manager_instance=command_manager_for_api)
agent_instance = agent.Agent(idea_synth=idea_synth_for_api, code_generator=code_generator, skill_manager=skill_manager_for_api) 

# --- Define Request/Response Models ---
class GenerationRequest(BaseModel):
    prompt: str

class TestGenerationRequest(BaseModel):
    filepath: str

class ModularityWarning(BaseModel):
    filepath: str
    message: str

class ModularityWarningsResponse(BaseModel):
    warnings: list[ModularityWarning]

# --- Add these to your Pydantic Models ---
class ScaffoldLocalRequest(BaseModel):
 project_name: str
 project_brief: dict[str, Any]

class CreateRepoRequest(BaseModel):
 repo_name: str
 description: str
 private: bool = True

class ScaffoldResponse(BaseModel):
 success: bool
 message: str
# 1. Add these new Pydantic models at the top with the others
class RefactorRequest(BaseModel):
    code_content: str # Changed from filepath to code_content
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

# New Pydantic models for GitHub file browsing
class GitHubRepoRequest(BaseModel):
    owner: str
    repo: str

class GitHubFileRequest(BaseModel):
    owner: str
    repo: str
    filepath: str

# New Pydantic models for User Profile
class ProfileSetRequest(BaseModel):
    category: str
    key: str
    value: Any # Allow any type, including dict for providers

class ProfileResponse(BaseModel):
    profile: dict | None = None
    message: str | None = None

# New Pydantic models for Feedback
class FeedbackSubmitRequest(BaseModel): # Renamed to avoid confusion with internal models
    rating: int # e.g., 5, 3, 1
    comment: str = ""
    context_id: str | None = None # Optional context_id

class LastInteractionResponse(BaseModel):
    interaction: dict[str, Any] | None = None # Use dict[str, Any] for clarity
    message: str | None = None

# Pydantic model for setting focus
class SetFocusRequest(BaseModel):
    focus_text: str | None = None # Allow None to clear focus

class FocusResponse(BaseModel):
    current_focus: str | None = None
    message: str

# Define request/response models for the new endpoint
class GenerateReadmeRequest(BaseModel):
    project_brief: dict[str, Any]

class GenerateReadmeResponse(BaseModel):
    readme_content: str

# Define request/response models
class GenerateRoadmapRequest(BaseModel):
    project_brief: dict[str, Any]

class GenerateRoadmapResponse(BaseModel):
    roadmap_content: str

# Add with other Pydantic models
class StyleUpdateRequest(BaseModel):
    category: str
    settings: dict[str, Any]

class StyleUpdateResponse(BaseModel):
    message: str
    updated_preferences: dict[str, Any]
# Add with other Pydantic models
class StyleUpdateRequest(BaseModel):
    category: str
    settings: dict[str, Any]

class StyleUpdateResponse(BaseModel):
    message: str
    updated_preferences: dict[str, Any]

# --- Add with other Pydantic Models ---
class RandomIdeaResponse(BaseModel):
    idea: str
# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to The Giblet API. Navigate to /docs for details."}

@app.get("/roadmap")
def get_roadmap():
    return {"roadmap": roadmap_manager.get_tasks()}

# <<< NEW ENDPOINTS
# --- Add these new endpoints to your API file ---
@app.post("/project/scaffold_local", response_model=ScaffoldResponse)
def scaffold_local_project_endpoint(request: ScaffoldLocalRequest):
    """
    Creates a new project structure on the local filesystem.
    """
    if not request.project_name or not request.project_brief:
        raise HTTPException(status_code=400, detail="Project name and brief are required.")

    # The base_path can be configured or defaulted to the project's root
    project_path = project_scaffolder_api.scaffold_local(
        project_name=request.project_name,
        project_brief=request.project_brief,
        base_path=Path.cwd() # Or another configurable path
    )

    if project_path:
        return ScaffoldResponse(success=True, message="Local project scaffolded successfully.", path=str(project_path))
    else:
        raise HTTPException(status_code=500, detail="Failed to scaffold local project.")

@app.post("/project/create_github_repo", response_model=ScaffoldResponse)
def create_github_repo_endpoint(request: CreateRepoRequest):
    """
    Creates a new repository on GitHub.
    """
    if not request.repo_name:
        raise HTTPException(status_code=400, detail="Repository name is required.")

    result = github_client_api.create_repo(
        repo_name=request.repo_name,
        description=request.description,
        private=request.private
    )

    if result and "html_url" in result:
        return ScaffoldResponse(success=True, message=f"GitHub repository created: {result['html_url']}")
    else:
        raise HTTPException(status_code=500, detail="Failed to create GitHub repository.")

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
    """Generates a refactoring of provided code content, and returns both versions."""
    original_code = request.code_content # Directly use code_content
    if not original_code.strip():
        raise HTTPException(status_code=400, detail="Code content cannot be empty.")
    
    refactor_result = code_generator.refactor_code(original_code, request.instruction)
    refactored_code = refactor_result.get("refactored_code", f"# Error: No code returned from refactoring.\n{original_code}")
    explanation = refactor_result.get("explanation", "No explanation was provided.")

    return {
        "original_code": original_code,
        "refactored_code": refactored_code,
        "explanation": explanation
    }

@app.post("/file/write")
def write_file_endpoint(request: WriteFileRequest):
    """Safely writes content to a file."""
    if not request.filepath:
        raise HTTPException(status_code=400, detail="Filepath cannot be empty.")

    success = utils.write_file(request.filepath, request.content)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to write to file: {request.filepath}")

    # --- Modularity Check Logic ---
    try:
        exceeds, line_count = modularity_guardrails.check_file_length(request.filepath)
        warnings = memory.recall('modularity_warnings')
        if not isinstance(warnings, dict):
            warnings = {}

        if exceeds:
            warning_message = (
                f"File '{request.filepath}' is now {line_count} lines long. "
                "Consider refactoring it into smaller, more focused modules."
            )
            warnings[request.filepath] = warning_message
        elif request.filepath in warnings:
            # If the file was previously long but is now short, remove the warning
            del warnings[request.filepath]
        memory.remember('modularity_warnings', warnings)
    except Exception as e:
        print(f"[API Modularity] Error during check for {request.filepath}: {e}")
    return {"message": "File updated successfully."}

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


# --- GitHub Browsing Endpoints ---
@app.post("/github/repo/contents")
def github_repo_contents_endpoint(request: GitHubRepoRequest):
    """Lists all files in a given GitHub repository."""
    contents = github_client_api.list_repo_contents(owner=request.owner, repo=request.repo)
    if isinstance(contents, dict) and "error" in contents:
        raise HTTPException(status_code=contents.get("status_code", 500), detail=contents["error"])
    return {"files": contents}

@app.post("/github/repo/file")
def github_file_content_endpoint(request: GitHubFileRequest):
    """Gets the content of a specific file from a GitHub repository."""
    file_data = github_client_api.get_file_content(owner=request.owner, repo=request.repo, filepath=request.filepath)
    if "error" in file_data:
        raise HTTPException(status_code=file_data.get("status_code", 500), detail=file_data["error"])
    return file_data
# --- User Profile API Endpoints ---
@app.get("/profile", response_model=ProfileResponse)
def get_user_profile_endpoint():
    """Retrieves the entire user profile."""
    data = user_profile_instance.get_all_data()
    return ProfileResponse(profile=data)

@app.post("/profile/set", response_model=ProfileResponse)
def set_user_profile_endpoint(request: ProfileSetRequest):
    """Sets a specific preference in the user profile."""
    user_profile_instance.add_preference(request.category, request.key, request.value)
    return ProfileResponse(message=f"Preference '{request.category}.{request.key}' set to '{request.value}'.")

@app.post("/profile/clear", response_model=ProfileResponse)
def clear_user_profile_endpoint():
    """Clears the entire user profile."""
    user_profile.clear_profile()
    return ProfileResponse(message="User profile cleared successfully.")


@app.get("/feedback/last_interaction", response_model=LastInteractionResponse)
def get_last_ai_interaction_endpoint():
    """Retrieves the last AI interaction stored in memory."""
    interaction = memory.recall('last_ai_interaction')
    if interaction and isinstance(interaction, dict):
        return LastInteractionResponse(interaction=interaction)
    return LastInteractionResponse(message="No recent AI interaction found in memory.", interaction=None)

@app.post("/feedback", response_model=ProfileResponse)
async def submit_feedback_endpoint(request: FeedbackSubmitRequest): # Use the new request model
    """Submits feedback, optionally including a context_id."""
    try:
        # UserProfile.add_feedback expects rating as int, comment as str, and context_id as str | None
        user_profile_instance.add_feedback(request.rating, request.comment, context_id=request.context_id)
        # Optionally clear last_ai_interaction from memory if it's always tied to feedback submission
        # memory.remember('last_ai_interaction', None) 
        return ProfileResponse(message="Feedback submitted successfully!")
    except Exception as e:
        # Consider logging the exception e
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")


# --- Memory/Focus API Endpoints ---
@app.get("/memory/focus", response_model=FocusResponse)
def get_focus_endpoint():
    current_focus = memory.recall("current_focus")
    if isinstance(current_focus, str) and not current_focus.startswith("I don't have a memory for"):
        return FocusResponse(current_focus=current_focus, message="Current focus retrieved.")
    return FocusResponse(current_focus=None, message="No current focus is set.")

@app.post("/memory/focus", response_model=FocusResponse)
def set_focus_endpoint(request: SetFocusRequest):
    if request.focus_text is None or request.focus_text.strip() == "":
        memory.remember("current_focus", None) # Clear focus
        return FocusResponse(current_focus=None, message="Focus cleared.")
    else:
        memory.remember("current_focus", request.focus_text)
        return FocusResponse(current_focus=request.focus_text, message=f"Focus set to: {request.focus_text}")


# ... add with other endpoints ...

@app.post("/generate/readme", response_model=GenerateReadmeResponse)
def generate_readme_endpoint(request: GenerateReadmeRequest):
    """Generates a project README from a project brief."""
    if not request.project_brief:
        raise HTTPException(status_code=400, detail="Project brief cannot be empty.")
    
    content = readme_generator_for_api.generate(request.project_brief)
    
    if "Failed" in content or "Error" in content:
        raise HTTPException(status_code=500, detail=content)
        
    return GenerateReadmeResponse(readme_content=content)


# ... add with other endpoints ...

@app.post("/generate/roadmap", response_model=GenerateRoadmapResponse)
def generate_roadmap_endpoint(request: GenerateRoadmapRequest):
    """Generates a project roadmap from a project brief."""
    if not request.project_brief:
        raise HTTPException(status_code=400, detail="Project brief cannot be empty.")
    
    content = roadmap_generator_for_api.generate(request.project_brief)
    
    if "Failed" in content or "Error" in content:
        raise HTTPException(status_code=500, detail=content)
        
    return GenerateRoadmapResponse(roadmap_content=content)

# Add with other endpoints
@app.post("/style/set_preferences", response_model=StyleUpdateResponse)
def set_style_preferences_endpoint(request: StyleUpdateRequest):
    """Sets a whole category of style preferences at once."""
    try:
        # Note: The StylePreferenceManager class handles the dot-notation logic.
        style_manager_for_api.set_preferences_for_category(request.category, request.settings)
        
        updated_prefs = style_manager_for_api.get_all_preferences()
        return StyleUpdateResponse(
            message=f"'{request.category}' style preferences updated successfully.",
            updated_preferences=updated_prefs
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Add this new endpoint to your API file ---
@app.post("/ideas/random_weird", response_model=RandomIdeaResponse)
def get_random_weird_idea_endpoint():
    """
    Generates a single, random, weird project idea using the IdeaSynthesizer.
    """
    # The prompt for a random idea can be simple and open-ended.
    random_prompt = "a strange and wonderful new software project"
    
    # Use the existing idea_synth_for_api instance
    idea = idea_synth_for_api.generate_ideas(random_prompt, weird_mode=True)
    
    if not idea or "Could not get a response" in idea:
        raise HTTPException(status_code=500, detail="Failed to generate a random idea from the LLM.")
        
    # The idea synth might return a list or formatted text, let's just grab the first line.
    first_idea = idea.splitlines()[0] if idea else "A mysteriously blank idea." # Handle empty idea
    
    return RandomIdeaResponse(idea=first_idea)

@app.get("/modularity/warnings", response_model=ModularityWarningsResponse)
def get_modularity_warnings():
    """
    Retrieves current modularity warnings from memory.
    The dashboard can poll this endpoint to display non-intrusive warnings (e.g., toasts)
    when files become excessively long.
    """
    warnings_dict = memory.recall('modularity_warnings')
    if not isinstance(warnings_dict, dict):
        warnings_dict = {}
    
    warnings_list = [
        ModularityWarning(filepath=fp, message=msg) for fp, msg in warnings_dict.items()
    ]
    return ModularityWarningsResponse(warnings=warnings_list)

# --- Skill API Endpoints ---
@app.get("/skills/list")
def list_skills_endpoint():
    """Lists all available skills."""
    return {"skills": skill_manager_for_api.list_skills()}

# --- Agent API Endpoints ---

MAX_API_FIX_ATTEMPTS = 3

@app.post("/agent/plan", response_model=AgentPlanResponse)
def agent_create_plan_endpoint(request: AgentPlanRequest):
    """
    Creates a multi-step plan for the agent to achieve a goal.
    The plan is also stored in memory for potential execution.
    """
    plan = agent_instance.create_plan(request.goal) # Use agent_instance
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

        # Use the API's instance of CommandManager
        execution_result = command_manager_for_api.execute(command_name, cmd_args)

        return_code, stdout, stderr = 0, "", ""
        if isinstance(execution_result, tuple) and len(execution_result) == 3:
            return_code, stdout, stderr = execution_result
        
        is_test_step = (command_name == "exec" and cmd_args and "pytest" in " ".join(cmd_args))

        if is_test_step and return_code != 0:
            tests_failed_count +=1
            current_error_log = stdout + stderr # Capture initial error log
            # Use the API's instance of CommandManager
            current_return_code, retry_stdout, retry_stderr = command_manager_for_api.execute("exec", cmd_args)

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
                        fixed_code = agent_instance.attempt_fix(code_to_fix, current_error_log) # Use agent_instance
                        print(f"   └─ [API] Proposed fix by LLM for {file_to_test}:\n-------\n{fixed_code}\n-------")
                        
                        has_actual_code = any(line.strip() and not line.strip().startswith("#") for line in fixed_code.splitlines())
                        if fixed_code and has_actual_code:
                            utils.write_file(file_to_test, fixed_code)
                            print(f"   └─ [API] Applied potential fix to {file_to_test}. Retrying tests...") # Use command_manager_for_api consistently
                            current_return_code, retry_stdout, retry_stderr = command_manager_for_api.execute("exec", cmd_args)
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