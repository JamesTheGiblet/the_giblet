# core/capability_assessor.py
import json
import subprocess
import tempfile
import sys  # For sys.executable
from pathlib import Path
from typing import Dict, Any

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
            "details": {}
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
