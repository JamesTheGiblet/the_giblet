# core/capability_assessor.py
import json
import subprocess
import tempfile
import sys  # For sys.executable
from pathlib import Path
from typing import Dict, Any
import random # For generating haystack

from core.code_generator import CodeGenerator  # Assumes CodeGenerator has generate_function and generate_text
from core.idea_synth import IdeaSynthesizer  # For general text generation tasks like JSON
from core.llm_provider_base import LLMProvider  # To get model name

GAUNTLET_FILE_PATH = Path(__file__).parent.parent / "data" / "gauntlet.json"

class CapabilityAssessor:
    def __init__(self, llm_provider: LLMProvider, code_generator: CodeGenerator, idea_synthesizer: IdeaSynthesizer):
        self.llm_provider = llm_provider
        self.code_gen = code_generator
        self.idea_synth = idea_synthesizer

        if not GAUNTLET_FILE_PATH.exists():
            raise FileNotFoundError(f"Gauntlet definition file not found at {GAUNTLET_FILE_PATH}")
        with open(GAUNTLET_FILE_PATH, 'r', encoding='utf-8') as f:
            self.gauntlet_tests = json.load(f)
        print("\U0001F52C Capability Assessor initialized.")

    def run_gauntlet(self, dry_run: bool = False) -> Dict[str, Any]:
        print(f"\U0001F52C Running Capability Gauntlet for LLM: {self.llm_provider.PROVIDER_NAME} - {self.llm_provider.model_name}...")
        profile = {
            "provider_name": self.llm_provider.PROVIDER_NAME,
            "model_name": self.llm_provider.model_name,
            "capabilities": {},
            "details": {},
            "determined_capabilities": {} # This will store direct capability values
        }

        # --- Test Code Generation ---
        cg_tests = sorted(self.gauntlet_tests.get("code_generation", []), key=lambda x: x['level'])
        profile["capabilities"]["code_generation_level"] = 0
        profile["details"]["code_generation"] = []

        for test in cg_tests:
            print(f"   └─ Testing Code Gen Level {test['level']}...")
            if dry_run:
                print(f"      [DRY RUN] Prompt: {test['prompt']}")
                continue

            generated_code = self.code_gen.generate_function(test['prompt'])
            try:
                func_name = generated_code.split('def ')[1].split('(')[0].strip()
                if not func_name.isidentifier():
                    print(f"      └─ ❌ Level {test['level']} Failed. Invalid function name.")
                    break
            except IndexError:
                print(f"      └─ ❌ Level {test['level']} Failed. Could not parse function.")
                break

            passed = self._validate_code(generated_code, test['validation_test'], func_name)
            profile["details"]["code_generation"].append({
                "level": test["level"],
                "prompt": test["prompt"],
                "output": generated_code,
                "passed": passed
            })

            if passed:
                print(f"      └─ ✅ Level {test['level']} Passed.")
                profile["capabilities"]["code_generation_level"] = test['level']
            else:
                print(f"      └─ ❌ Level {test['level']} Failed. Stopping code_generation assessment.")
                break

        # --- Test JSON Adherence ---
        json_tests = sorted(self.gauntlet_tests.get("json_adherence", []), key=lambda x: x['level'])
        profile["capabilities"]["json_adherence_level"] = 0
        profile["details"]["json_adherence"] = []

        for test in json_tests:
            print(f"   └─ Testing JSON Adherence Level {test['level']}...")
            if dry_run:
                print(f"      [DRY RUN] Prompt: {test['prompt']}")
                continue

            llm_response = self.idea_synth.generate_text(test['prompt'])
            validation_type = test.get("validation_type")
            passed = False

            if validation_type == "is_json_exact":
                passed = self._validate_json_exact(llm_response, test.get("expected_json"))

            profile["details"]["json_adherence"].append({
                "level": test["level"],
                "prompt": test["prompt"],
                "response": llm_response,
                "passed": passed
            })

            if passed:
                print(f"      └─ ✅ Level {test['level']} Passed.")
                profile["capabilities"]["json_adherence_level"] = test['level']
            else:
                print(f"      └─ ❌ Level {test['level']} Failed. Stopping json_adherence assessment.")
                break

        # Populate determined_capabilities based on test results
        # This is a simple example; more sophisticated mapping can be added as gauntlet expands
        if profile["capabilities"].get("json_adherence_level", 0) > 0:
            # If JSON tests passed, we can be more confident in asking for JSON.
            # This might influence how LLMCapabilities reports 'output_formats'.
            # For direct override, LLMCapabilities needs to merge this carefully.
            profile["determined_capabilities"]["output_formats_include_json"] = True # Custom flag
        if profile["capabilities"].get("code_generation_level", 0) >= 1: # Example
            profile["determined_capabilities"]["can_generate_functions"] = True # Custom flag
        
        # --- Test Context Window Recall ---
        ctx_tests = sorted(self.gauntlet_tests.get("context_window_recall", []), key=lambda x: x['level'])
        profile["capabilities"]["context_window_recall_level"] = 0
        profile["details"]["context_window_recall"] = []

        for test in ctx_tests:
            print(f"   └─ Testing Context Recall Level {test['level']} (Haystack: {test.get('haystack_size_kb')}KB)...")
            if dry_run:
                print(f"      [DRY RUN] Prompt template: {test['prompt_template']}, Needle: {test['needle']}")
                continue

            haystack = self._generate_haystack(test.get("haystack_size_kb", 1) * 1024) # Approx KB to chars
            prompt = test["prompt_template"].replace("{needle}", test["needle"]).replace("{haystack}", haystack)
            
            llm_response = self.idea_synth.generate_text(prompt) # Use idea_synth for general text
            passed = False
            if test.get("validation_type") == "exact_match_needle":
                passed = self._validate_needle_in_haystack(llm_response, test["needle"])

            profile["details"]["context_window_recall"].append({
                "level": test["level"],
                "prompt_length_approx_chars": len(prompt),
                "response": llm_response[:200], # Store a snippet of the response
                "passed": passed
            })

            if passed:
                print(f"      └─ ✅ Level {test['level']} Passed.")
                profile["capabilities"]["context_window_recall_level"] = test['level']
            else:
                print(f"      └─ ❌ Level {test['level']} Failed. Stopping context_window_recall assessment.")
                break
        
        # --- Test Instruction Following ---
        instr_tests = sorted(self.gauntlet_tests.get("instruction_following", []), key=lambda x: x['level'])
        profile["capabilities"]["instruction_following_level"] = 0
        profile["details"]["instruction_following"] = []

        for test in instr_tests:
            print(f"   └─ Testing Instruction Following Level {test['level']}...")
            if dry_run:
                print(f"      [DRY RUN] Prompt: {test['prompt']}")
                continue
            
            llm_response = self.idea_synth.generate_text(test['prompt'])
            passed = False
            if test.get("validation_type") == "multi_constraint_check":
                passed, constraint_results = self._validate_multi_constraints(llm_response, test.get("constraints", []))
                profile["details"]["instruction_following"].append({
                    "level": test["level"],
                    "prompt": test["prompt"],
                    "response": llm_response,
                    "passed": passed,
                    "constraint_results": constraint_results
                })
            else: # Fallback for unknown validation type for this category
                 profile["details"]["instruction_following"].append({
                    "level": test["level"],
                    "prompt": test["prompt"],
                    "response": llm_response,
                    "passed": False, # Cannot validate
                    "constraint_results": "Unknown validation_type"
                })

            if passed:
                print(f"      └─ ✅ Level {test['level']} Passed.")
                profile["capabilities"]["instruction_following_level"] = test['level']
            else:
                print(f"      └─ ❌ Level {test['level']} Failed. Stopping instruction_following assessment.")
                break

        print("\U0001F52C Gauntlet finished. Capability Profile generated.")
        return profile

    def _validate_code(self, code_to_test: str, test_code: str, func_name: str) -> bool:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            code_file = tmp_path / "module_to_test.py"
            test_file = tmp_path / "test_the_module.py"

            code_file.write_text(code_to_test, encoding='utf-8')
            full_test_code = f"from module_to_test import {func_name}\n\n{test_code}"
            test_file.write_text(full_test_code, encoding='utf-8')

            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_file)],
                capture_output=True, text=True, encoding='utf-8'
            )
            return result.returncode == 0

    def _validate_json_exact(self, response_text: str, expected_json: Dict[str, Any]) -> bool:
        try:
            parsed_json = json.loads(response_text.strip())
            return parsed_json == expected_json
        except json.JSONDecodeError:
            print(f"        └─ Failed to parse JSON: {response_text[:100]}...")
            return False
        except Exception as e:
            print(f"        └─ Error during JSON validation: {e}")
            return False

    def _generate_haystack(self, num_chars: int) -> str:
        """Generates a random string of approximately num_chars characters."""
        # Simple haystack generator, can be made more sophisticated
        words = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota", "kappa",
                 "lambda", "mu", "nu", "xi", "omicron", "pi", "rho", "sigma", "tau", "upsilon",
                 "phi", "chi", "psi", "omega", "lorem", "ipsum", "dolor", "sit", "amet", "consectetur",
                 "adipiscing", "elit", "sed", "do", "eiusmod", "tempor", "incididunt", "ut", "labore",
                 "et", "dolore", "magna", "aliqua"]
        haystack = []
        current_len = 0
        while current_len < num_chars:
            word = random.choice(words)
            haystack.append(word)
            current_len += len(word) + 1 # +1 for space
        return " ".join(haystack)

    def _validate_needle_in_haystack(self, response_text: str, needle: str) -> bool:
        # Simple validation: check if the needle is exactly in the response,
        # and the response is not too long (to avoid the model just repeating the prompt).
        return needle in response_text and len(response_text) < (len(needle) + 50)

    def _validate_multi_constraints(self, response_text: str, constraints: list) -> tuple[bool, dict]:
        all_passed = True
        results = {}
        parsed_json_response = None

        for i, constraint in enumerate(constraints):
            ctype = constraint.get("type")
            value = constraint.get("value")
            key = constraint.get("key")
            json_path_str = constraint.get("json_path")
            item_index = constraint.get("item_index")
            constraint_passed = False
            detail = "Constraint not processed"

            try:
                if ctype == "word_count_exact":
                    constraint_passed = len(response_text.split()) == value
                    detail = f"Word count: {len(response_text.split())}, Expected: {value}"
                elif ctype == "starts_with":
                    constraint_passed = response_text.strip().startswith(value)
                    detail = f"Starts with '{value}'"
                elif ctype == "not_contains_char":
                    constraint_passed = str(value).lower() not in response_text.lower()
                    detail = f"Does not contain char '{value}'"
                elif ctype == "json_parsable":
                    parsed_json_response = json.loads(response_text.strip())
                    constraint_passed = True
                    detail = "JSON is parsable"
                # Add more constraint types here (json_has_key, list_length_exact, list_item_contains_text etc.)
                # This part can get quite complex and would need careful implementation for each constraint type.
                # For brevity, I'm not fully implementing all JSON pathing logic here.
            except Exception as e:
                detail = f"Error processing constraint: {e}"
                constraint_passed = False
            results[f"constraint_{i+1}_{ctype}"] = {"passed": constraint_passed, "detail": detail}
            if not constraint_passed:
                all_passed = False
        return all_passed, results
