# api.py
import os
import json
import random
from typing import Dict, Optional, Any

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import shlex
from dotenv import load_dotenv # Import load_dotenv
import logging
from pathlib import Path
import sys

# Add project root to sys.path to allow imports from core
sys.path.append(str(Path(__file__).resolve().parent))

# --- Import Core Modules ---
from core import user_profile as core_user_profile
from core.idea_synth import IdeaSynthesizer
from core.roadmap_manager import RoadmapManager
from core.idea_interpreter import IdeaInterpreter
from core.memory import Memory
from core.code_generator import CodeGenerator
from core.automator import Automator
from core import agent, command_manager, utils
from core.user_profile import UserProfile
from core.skill_manager import SkillManager
from core.llm_provider_base import LLMProvider
from core.github_client import GitHubClient
from core.project_scaffold import ProjectScaffolder
from core.readme_generator import ReadmeGenerator
from core.roadmap_generator import RoadmapGenerator
from core.llm_providers import GeminiProvider, OllamaProvider
from core.project_contextualizer import ProjectContextualizer
from core.modularity_guardrails import ModularityGuardrails
from core.style_preference import StylePreferenceManager
from core.idea_generator import get_random_weird_idea # <-- IMPORT NEW MODULE

# --- Setup Logger ---
logger = logging.getLogger(__name__)

# --- Initialize FastAPI and Core Modules ---
app = FastAPI(
    title="The Giblet API",
    description="API for interacting with The Giblet's core services.",
    version="0.1.0"
)
memory = Memory()
style_manager_for_api = StylePreferenceManager()
load_dotenv() # Load environment variables from .env file
roadmap_manager = RoadmapManager(memory_system=memory, style_preference_manager=style_manager_for_api)
user_profile_instance = UserProfile(memory_system=memory)
command_manager_for_api = command_manager.CommandManager(memory_system=memory)
modularity_guardrails = ModularityGuardrails()
automator = Automator()

# Helper function to get the configured LLM provider
def get_configured_llm_provider(profile: UserProfile) -> LLMProvider | None:
    active_provider_name = profile.get_preference("llm_provider_config", "active_provider", "gemini")
    raw_provider_configs = profile.get_preference("llm_provider_config", "providers")

    provider_configs = {}
    if isinstance(raw_provider_configs, dict):
        provider_configs = raw_provider_configs
    elif isinstance(raw_provider_configs, str) and raw_provider_configs.startswith("{") and raw_provider_configs.endswith("}"):
        try:
            provider_configs = json.loads(raw_provider_configs)
        except json.JSONDecodeError:
            logger.warning(f"Could not parse 'providers' config string from profile. Using defaults. String was: {raw_provider_configs}")
            provider_configs = core_user_profile.DEFAULT_PROFILE_STRUCTURE["llm_provider_config"]["providers"]
    else:
        logger.warning(f"'providers' config in profile is not a valid dictionary. Using defaults. Value was: {raw_provider_configs}")
        provider_configs = core_user_profile.DEFAULT_PROFILE_STRUCTURE["llm_provider_config"]["providers"]

    if active_provider_name == "gemini":
        gemini_config = provider_configs.get("gemini", {})
        api_key = gemini_config.get("api_key")
        model_name = gemini_config.get("model_name", "gemini-1.5-flash-latest")
        logger.info(f"Configuring GeminiProvider (model: {model_name}, API key from profile: {'yes' if api_key else 'no/use .env'})")
        return GeminiProvider(model_name=model_name, api_key=api_key if api_key else None)
    elif active_provider_name == "ollama":
        ollama_config = provider_configs.get("ollama", {})
        base_url = ollama_config.get("base_url", "http://localhost:11434")
        model_name = ollama_config.get("model_name", "mistral")
        logger.info(f"Configuring OllamaProvider (model: {model_name}, url: {base_url})")
        return OllamaProvider(model_name=model_name, base_url=base_url)
    else:
        logger.warning(f"Unknown LLM provider '{active_provider_name}' configured in profile. Defaulting to Gemini.")
        return GeminiProvider()

api_llm_provider = get_configured_llm_provider(user_profile_instance)

if not api_llm_provider or not api_llm_provider.is_available():
    logger.warning(f"Configured LLM provider ({api_llm_provider.PROVIDER_NAME if api_llm_provider else 'N/A'}) is not available. Operations requiring LLM will be affected.")
    if not (api_llm_provider and api_llm_provider.is_available()):
        logger.warning("Attempting fallback to Gemini (default) due to primary provider unavailability.")
        api_llm_provider = GeminiProvider()
        if not api_llm_provider.is_available():
            logger.warning("Fallback Gemini provider also not available. LLM features will be severely limited.")
            api_llm_provider = None

# --- Initialize Core Module Instances ---
readme_generator_api = ReadmeGenerator(llm_provider=api_llm_provider, style_manager=style_manager_for_api)
roadmap_generator_api = RoadmapGenerator(llm_provider=api_llm_provider, style_manager=style_manager_for_api)
github_client_api = GitHubClient()
project_scaffolder_api = ProjectScaffolder(
    readme_generator=readme_generator_api,
    roadmap_generator=roadmap_generator_api,
    style_manager=style_manager_for_api
)
project_contextualizer_api = ProjectContextualizer(memory_system=memory, project_root=".")
idea_synth_for_api = IdeaSynthesizer(
    user_profile=user_profile_instance,
    memory_system=memory,
    llm_provider=api_llm_provider,
    project_contextualizer=project_contextualizer_api,
    style_preference_manager=style_manager_for_api
)

# Initialize ReadmeGenerator and RoadmapGenerator
readme_generator_instance = ReadmeGenerator(llm_provider=api_llm_provider, style_manager=style_manager_for_api)
roadmap_generator_instance = RoadmapGenerator(llm_provider=api_llm_provider, style_manager=style_manager_for_api)

code_generator = CodeGenerator(user_profile=user_profile_instance, memory_system=memory, llm_provider=api_llm_provider, project_contextualizer=project_contextualizer_api)
idea_interpreter_instance = IdeaInterpreter(llm_provider=api_llm_provider, user_profile=user_profile_instance, memory=memory, style_manager=style_manager_for_api, project_contextualizer=project_contextualizer_api,
                                            readme_generator=readme_generator_instance, roadmap_generator=roadmap_generator_instance)
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
    path: Optional[str] = None # Make path optional

class RefactorRequest(BaseModel):
    code_content: str
    instruction: str

class WriteFileRequest(BaseModel):
    filepath: str
    content: str

class StubRequest(BaseModel):
    filepath: str

class AgentPlanRequest(BaseModel):
    goal: str

class AgentPlanResponse(BaseModel):
    plan: list[str] | None = None
    error: str | None = None

class AgentExecuteResponse(BaseModel):
    message: str
    steps_executed: int
    tests_failed_initial: int
    fix_attempts: int
    self_correction_successful: bool | None = None
    final_error: str | None = None


class GitHubRepoRequest(BaseModel):
    owner: str
    repo: str

class GitHubFileRequest(BaseModel):
    owner: str
    repo: str
    filepath: str

class ProfileSetRequest(BaseModel):
    category: str
    key: str
    value: Any

class ProfileResponse(BaseModel):
    profile: dict | None = None
    message: str | None = None

class FeedbackSubmitRequest(BaseModel):
    rating: int
    comment: str = ""
    context_id: str | None = None

class LastInteractionResponse(BaseModel):
    interaction: dict[str, Any] | None = None
    message: str | None = None

class SetFocusRequest(BaseModel):
    focus_text: str | None = None

class FocusResponse(BaseModel):
    current_focus: str | None = None
    message: str

class GenerateReadmeRequest(BaseModel):
    project_brief: dict[str, Any]

class GenerateReadmeResponse(BaseModel):
    readme_content: str

class GenerateRoadmapRequest(BaseModel):
    project_brief: dict[str, Any]

class GenerateRoadmapResponse(BaseModel):
    roadmap_content: str

class StyleUpdateRequest(BaseModel):
    category: str
    settings: dict[str, Any]

class StyleUpdateResponse(BaseModel):
    message: str
    updated_preferences: dict[str, Any]

class StylePreferencesResponse(BaseModel):
    preferences: dict[str, Any]

class DirectoryListResponse(BaseModel):
    directories: list[str]

class RandomIdeaResponse(BaseModel):
    idea: str

class GenesisStartRequest(BaseModel):
    initial_idea: str

class GenesisStartResponse(BaseModel):
    questions: str

class GenesisAnswerRequest(BaseModel):
    answer: str

class GenesisAnswerResponse(BaseModel):
    status: str
    data: Any
    message: str | None = None

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to The Giblet API. Navigate to /docs for details."}

@app.get("/roadmap")
def get_roadmap():
    return {"roadmap": roadmap_manager.get_tasks()}

@app.get("/ideas/random_weird", response_model=RandomIdeaResponse)
def get_random_weird_idea_endpoint():
    """
    Generates a single, random, weird project idea using the local static generator.
    """
    try:
        idea = get_random_weird_idea()
        return RandomIdeaResponse(idea=idea)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating random idea: {e}")

@app.post("/project/scaffold_local", response_model=ScaffoldResponse)
def scaffold_local_project_endpoint(request: ScaffoldLocalRequest):
    if not request.project_name or not request.project_brief:
        raise HTTPException(status_code=400, detail="Project name and brief are required.")
    project_path = project_scaffolder_api.scaffold_local(
        project_name=request.project_name,
        project_brief=request.project_brief,
        base_path=Path.cwd()
    )
    if project_path:
        return ScaffoldResponse(success=True, message="Local project scaffolded successfully.", path=str(project_path))
    else:
        raise HTTPException(status_code=500, detail="Failed to scaffold local project.")

@app.post("/project/create_github_repo", response_model=ScaffoldResponse)
def create_github_repo_endpoint(request: CreateRepoRequest):
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

@app.get("/project/directories", response_model=DirectoryListResponse)
def list_directories_endpoint():
    """
    Lists all directories in the project root, ignoring common build/cache folders.
    Note: This assumes a 'utils.list_directories()' function exists in 'core/utils.py'.
    """
    try:
        # This function will need to be implemented in your utils module.
        # It should scan the project root and return a list of directory paths.
        directories = utils.list_directories()
        return DirectoryListResponse(directories=directories)
    except AttributeError:
        raise HTTPException(status_code=501, detail="The function 'list_directories' is not implemented in the server's 'utils' module.")
    except Exception as e:
        logger.exception("Failed to list project directories.")
        raise HTTPException(status_code=500, detail=f"An error occurred while listing directories: {e}")

@app.post("/generate/function")
def generate_function_endpoint(request: GenerationRequest):
    code = code_generator.generate_function(request.prompt)
    return {"generated_code": code}

@app.post("/generate/tests")
def generate_tests_endpoint(request: TestGenerationRequest):
    source_code = utils.read_file(request.filepath)
    if not source_code:
        return {"error": "File not found or is empty."}
    tests = code_generator.generate_unit_tests(source_code, request.filepath)
    return {"generated_code": tests}

@app.post("/refactor")
def refactor_code_endpoint(request: RefactorRequest):
    original_code = request.code_content
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
    if not request.filepath:
        raise HTTPException(status_code=400, detail="Filepath cannot be empty.")
    success = utils.write_file(request.filepath, request.content)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to write to file: {request.filepath}")
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
            del warnings[request.filepath]
        memory.remember('modularity_warnings', warnings)
    except Exception as e:
        print(f"[API Modularity] Error during check for {request.filepath}: {e}")
    return {"message": "File updated successfully."}

@app.get("/files/list")
def list_files_endpoint():
    files = utils.list_files()
    return {"files": files}

@app.get("/file/read")
def read_file_endpoint(filepath: str):
    content = utils.read_file(filepath)
    if content is None:
        return {"error": "File not found or could not be read."}
    return {"filepath": filepath, "content": content}

@app.post("/automate/changelog")
def generate_changelog_endpoint():
    success = automator.generate_changelog()
    if success:
        return {"message": "Changelog generated successfully in data/changelogs/"}
    return {"error": "Failed to generate changelog."}

@app.post("/automate/stubs")
def generate_stubs_endpoint(request: StubRequest):
    success = automator.generate_stubs(request.filepath)
    if success:
        return {"message": f"Stub generation complete for {request.filepath}."}
    return {"error": f"Failed to generate stubs for {request.filepath}."}

@app.post("/github/repo/contents")
def github_repo_contents_endpoint(request: GitHubRepoRequest):
    contents = github_client_api.list_repo_contents(owner=request.owner, repo=request.repo)
    if isinstance(contents, dict) and "error" in contents:
        raise HTTPException(status_code=contents.get("status_code", 500), detail=contents["error"])
    return {"files": contents}

@app.post("/github/repo/file")
def github_file_content_endpoint(request: GitHubFileRequest):
    file_data = github_client_api.get_file_content(owner=request.owner, repo=request.repo, filepath=request.filepath)
    if "error" in file_data:
        raise HTTPException(status_code=file_data.get("status_code", 500), detail=file_data["error"])
    return file_data

@app.get("/profile", response_model=ProfileResponse)
def get_user_profile_endpoint():
    data = user_profile_instance.get_all_data()
    return ProfileResponse(profile=data)

@app.post("/profile/set", response_model=ProfileResponse)
def set_user_profile_endpoint(request: ProfileSetRequest):
    user_profile_instance.add_preference(request.category, request.key, request.value)
    return ProfileResponse(message=f"Preference '{request.category}.{request.key}' set to '{request.value}'.")

@app.post("/profile/clear", response_model=ProfileResponse)
def clear_user_profile_endpoint():
    user_profile_instance.clear_profile()
    return ProfileResponse(message="User profile cleared successfully.")

@app.get("/feedback/last_interaction", response_model=LastInteractionResponse)
def get_last_ai_interaction_endpoint():
    interaction = memory.recall('last_ai_interaction')
    if interaction and isinstance(interaction, dict):
        return LastInteractionResponse(interaction=interaction)
    return LastInteractionResponse(message="No recent AI interaction found in memory.", interaction=None)

@app.post("/feedback", response_model=ProfileResponse)
async def submit_feedback_endpoint(request: FeedbackSubmitRequest):
    try:
        user_profile_instance.add_feedback(request.rating, request.comment, context_id=request.context_id)
        return ProfileResponse(message="Feedback submitted successfully!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")

@app.get("/memory/focus", response_model=FocusResponse)
def get_focus_endpoint():
    current_focus = memory.recall("current_focus")
    if isinstance(current_focus, str) and not current_focus.startswith("I don't have a memory for"):
        return FocusResponse(current_focus=current_focus, message="Current focus retrieved.")
    return FocusResponse(current_focus=None, message="No current focus is set.")

@app.post("/memory/focus", response_model=FocusResponse)
def set_focus_endpoint(request: SetFocusRequest):
    if request.focus_text is None or request.focus_text.strip() == "":
        memory.remember("current_focus", None)
        return FocusResponse(current_focus=None, message="Focus cleared.")
    else:
        memory.remember("current_focus", request.focus_text)
        return FocusResponse(current_focus=request.focus_text, message=f"Focus set to: {request.focus_text}")

@app.post("/generate/readme", response_model=GenerateReadmeResponse)
def generate_readme_endpoint(request: GenerateReadmeRequest):
    if not request.project_brief:
        raise HTTPException(status_code=400, detail="Project brief cannot be empty.")
    # readme_generator_api.generate returns (content, style_used_dict), we only need content here
    content, _ = readme_generator_api.generate(request.project_brief)
    if "Failed" in content or "Error" in content:
        raise HTTPException(status_code=500, detail=content)
    return GenerateReadmeResponse(readme_content=content)

@app.post("/generate/roadmap", response_model=GenerateRoadmapResponse)
def generate_roadmap_endpoint(request: GenerateRoadmapRequest):
    if not request.project_brief:
        raise HTTPException(status_code=400, detail="Project brief cannot be empty.")
    content = roadmap_generator_api.generate(request.project_brief)
    if "Failed" in content or "Error" in content:
        raise HTTPException(status_code=500, detail=content)
    return GenerateRoadmapResponse(roadmap_content=content)

@app.post("/style/set_preferences", response_model=StyleUpdateResponse)
def set_style_preferences_endpoint(request: StyleUpdateRequest):
    try:
        style_manager_for_api.set_preferences_for_category(request.category, request.settings)
        updated_prefs = style_manager_for_api.get_all_preferences()
        return StyleUpdateResponse(
            message=f"'{request.category}' style preferences updated successfully.",
            updated_preferences=updated_prefs
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/genesis/start", response_model=GenesisStartResponse)
def genesis_start_endpoint(request: GenesisStartRequest):
    """
    Starts a new project idea interpretation session.
    """
    try:
        # Use the correct, non-deprecated method name.
        questions = idea_interpreter_instance.start_interpretation_session(request.initial_idea)
        if questions:
            return GenesisStartResponse(questions=questions)
        else:
            raise HTTPException(status_code=500, detail="LLM failed to generate initial questions for the interview.")
    except AttributeError:
        raise HTTPException(status_code=500, detail="The 'IdeaInterpreter' object in the current runtime does not have a 'start_interpretation_session' method. Please ensure the server is running the latest version of 'core/idea_interpreter.py'.")
    except Exception as e:
        logger.exception("An unexpected error occurred while starting the genesis interview.")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while starting the genesis interview: {e}")

@app.post("/genesis/answer", response_model=GenesisAnswerResponse)
def genesis_answer_endpoint(request: GenesisAnswerRequest):
    try:
        result = idea_interpreter_instance.submit_answer_and_continue(request.answer)
        if "status" not in result or "data" not in result:
            raise ValueError("IdeaInterpreter.submit_answer_and_continue did not return expected 'status' and 'data'.")
        return GenesisAnswerResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing genesis answer: {e}")

@app.get("/style/preferences", response_model=StylePreferencesResponse)
def get_style_preferences_endpoint():
    """
    Retrieves all current style preferences.
    """
    try:
        all_prefs = style_manager_for_api.get_all_preferences()
        return StylePreferencesResponse(preferences=all_prefs)
    except Exception as e:
        logger.exception("Failed to retrieve style preferences.")
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching style preferences: {e}")

@app.get("/modularity/warnings", response_model=ModularityWarningsResponse)
def get_modularity_warnings():
    warnings_dict = memory.recall('modularity_warnings')
    if not isinstance(warnings_dict, dict):
        warnings_dict = {}
    warnings_list = [
        ModularityWarning(filepath=fp, message=msg) for fp, msg in warnings_dict.items()
    ]
    return ModularityWarningsResponse(warnings=warnings_list)

@app.get("/skills/list")
def list_skills_endpoint():
    return {"skills": skill_manager_for_api.list_skills()}

@app.post("/agent/plan", response_model=AgentPlanResponse)
def agent_create_plan_endpoint(request: AgentPlanRequest):
    plan = agent_instance.create_plan(request.goal)
    if plan and not (isinstance(plan, list) and len(plan) > 0 and "Failed to generate" in plan[0]):
        memory.remember('api_last_plan', plan)
        return AgentPlanResponse(plan=plan)
    elif isinstance(plan, list) and len(plan) > 0:
        return AgentPlanResponse(error=plan[0])
    else:
        return AgentPlanResponse(error="Failed to generate a plan or the plan was empty.")

@app.post("/agent/execute", response_model=AgentExecuteResponse)
def agent_execute_plan_endpoint():
    plan = memory.recall('api_last_plan')
    if not isinstance(plan, list) or not plan:
        return AgentExecuteResponse(message="Execution failed: No plan found in API memory.", steps_executed=0, tests_failed_initial=0, fix_attempts=0, final_error="No plan available. Please generate a plan first using the /agent/plan endpoint.")

    steps_executed = 0
    tests_failed_count = 0
    fix_attempts_count = 0
    correction_successful = None
    final_plan_error = None
    MAX_API_FIX_ATTEMPTS = 3

    for i, command_string in enumerate(plan, 1):
        steps_executed += 1
        print(f"\n[API Agent Execute] --- Running Step {i}: giblet {command_string} ---")
        parts = shlex.split(command_string)
        if not parts:
            print(f"   └─ Skipping empty command in plan (Step {i}).")
            continue
        command_name = parts[0].lower()
        cmd_args = parts[1:]
        execution_result = command_manager_for_api.execute(command_name, cmd_args)
        return_code, stdout, stderr = 0, "", ""
        if isinstance(execution_result, tuple) and len(execution_result) == 3:
            return_code, stdout, stderr = execution_result
        is_test_step = (command_name == "exec" and cmd_args and "pytest" in " ".join(cmd_args))

        if is_test_step and return_code != 0:
            tests_failed_count +=1
            current_error_log = stdout + stderr
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
                        fixed_code = agent_instance.attempt_fix(code_to_fix, current_error_log)
                        print(f"   └─ [API] Proposed fix by LLM for {file_to_test}:\n-------\n{fixed_code}\n-------")
                        has_actual_code = any(line.strip() and not line.strip().startswith("#") for line in fixed_code.splitlines())
                        if fixed_code and has_actual_code:
                            utils.write_file(file_to_test, fixed_code)
                            print(f"   └─ [API] Applied potential fix to {file_to_test}. Retrying tests...")
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
            if correction_successful or final_plan_error:
                break
    
    message = f"Plan execution completed in {steps_executed} steps."
    if final_plan_error:
        message = f"Plan execution completed with errors after {steps_executed} steps."
    elif correction_successful:
        message = f"Plan execution completed successfully in {steps_executed} steps, with self-correction."
    
    return AgentExecuteResponse(
        message=message,
        steps_executed=steps_executed,
        tests_failed_initial=tests_failed_count,
        fix_attempts=fix_attempts_count,
        self_correction_successful=correction_successful,
        final_error=final_plan_error
    )
