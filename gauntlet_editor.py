# gauntlet_editor.py
import streamlit as st
import json
from pathlib import Path
import uuid

GAUNTLET_FILE_PATH = Path(__file__).parent / "data" / "gauntlet.json"
DEFAULT_GAUNTLET_STRUCTURE = {
    "code_generation": [],
    "json_adherence": []
}

def load_gauntlet_data():
    if GAUNTLET_FILE_PATH.exists():
        try:
            with open(GAUNTLET_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.error(f"Error decoding JSON from {GAUNTLET_FILE_PATH}. Loading default structure.")
            return DEFAULT_GAUNTLET_STRUCTURE.copy()
    return DEFAULT_GAUNTLET_STRUCTURE.copy()

def save_gauntlet_data(data):
    try:
        with open(GAUNTLET_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        st.success(f"Gauntlet data saved to {GAUNTLET_FILE_PATH}")
    except Exception as e:
        st.error(f"Error saving gauntlet data: {e}")

def main():
    st.set_page_config(page_title="Gauntlet Test Editor", layout="wide")
    st.title("🛠️ Capability Gauntlet Test Editor")

    if 'gauntlet_data' not in st.session_state:
        st.session_state.gauntlet_data = load_gauntlet_data()

    data = st.session_state.gauntlet_data

    # --- Add New Category ---
    with st.sidebar.expander("Add New Category", expanded=False):
        new_category_name = st.text_input("New Category Name", key="new_cat_name")
        if st.button("Add Category", key="add_cat_btn"):
            if new_category_name and new_category_name not in data:
                data[new_category_name] = []
                st.rerun()
            elif not new_category_name:
                st.warning("Category name cannot be empty.")
            else:
                st.warning(f"Category '{new_category_name}' already exists.")

    for category_name, tests in list(data.items()): # Use list(data.items()) for safe iteration if deleting
        st.subheader(f"Category: {category_name}")

        if st.button(f"🗑️ Delete Category: {category_name}", key=f"del_cat_{category_name}"):
            if category_name in data:
                del data[category_name]
                st.rerun()

        for i, test in enumerate(tests):
            # Ensure each test has a unique ID for stable widget keys if not present
            if 'id' not in test:
                test['id'] = str(uuid.uuid4())

            exp_key = f"exp_{category_name}_{test['id']}"
            with st.expander(f"Test Level {test.get('level', 'N/A')} (ID: {test['id'][:8]})", expanded=False):
                test['level'] = st.number_input("Level", value=test.get('level', 1), min_value=1, key=f"level_{exp_key}")
                test['prompt'] = st.text_area("Prompt", value=test.get('prompt', ''), height=100, key=f"prompt_{exp_key}")

                if category_name == "code_generation":
                    test['validation_test'] = st.text_area("Validation Test (Pytest)", value=test.get('validation_test', ''), height=150, key=f"val_test_{exp_key}")
                elif category_name == "json_adherence":
                    test['validation_type'] = st.selectbox("Validation Type", options=["is_json_exact", "is_json_parsable"], index=["is_json_exact", "is_json_parsable"].index(test.get('validation_type', "is_json_exact")), key=f"val_type_{exp_key}")
                    expected_json_str = test.get('expected_json', {})
                    if isinstance(expected_json_str, (dict, list)): # If it's already an object
                        expected_json_str = json.dumps(expected_json_str, indent=2)

                    edited_expected_json_str = st.text_area("Expected JSON (as string)", value=expected_json_str, height=100, key=f"exp_json_{exp_key}")
                    try:
                        test['expected_json'] = json.loads(edited_expected_json_str) if edited_expected_json_str.strip() else {}
                    except json.JSONDecodeError:
                        st.error("Invalid JSON in 'Expected JSON' field. Please correct it.")
                        # Keep the string as is for the user to fix, or revert to previous valid if stored
                        test['expected_json'] = test.get('expected_json', {}) # Revert or keep old
                else:
                    # Generic handling for other/new categories: allow editing raw test data
                    st.json(test, expanded=True) # Display raw, could be made editable with more effort

                if st.button("🗑️ Delete Test", key=f"del_test_{exp_key}"):
                    tests.pop(i)
                    st.rerun()

        # --- Add New Test to Category ---
        with st.expander(f"Add New Test to '{category_name}'", expanded=False):
            new_test_level = st.number_input("Level", min_value=1, value=max([t.get('level', 0) for t in tests] + [0]) + 1, key=f"new_level_{category_name}")
            new_test_prompt = st.text_area("Prompt", height=100, key=f"new_prompt_{category_name}")
            
            new_test_validation_test = ""
            new_test_validation_type = "is_json_exact"
            new_test_expected_json_str = "{}"

            if category_name == "code_generation":
                new_test_validation_test = st.text_area("Validation Test (Pytest)", height=150, key=f"new_val_test_{category_name}")
            elif category_name == "json_adherence":
                new_test_validation_type = st.selectbox("Validation Type", options=["is_json_exact", "is_json_parsable"], key=f"new_val_type_{category_name}")
                new_test_expected_json_str = st.text_area("Expected JSON (as string)", value="{}", height=100, key=f"new_exp_json_{category_name}")

            if st.button(f"Add Test to {category_name}", key=f"add_test_btn_{category_name}"):
                if new_test_prompt:
                    new_test_entry = {
                        "id": str(uuid.uuid4()),
                        "level": new_test_level,
                        "prompt": new_test_prompt
                    }
                    if category_name == "code_generation":
                        new_test_entry["validation_test"] = new_test_validation_test
                    elif category_name == "json_adherence":
                        new_test_entry["validation_type"] = new_test_validation_type
                        try:
                            new_test_entry["expected_json"] = json.loads(new_test_expected_json_str) if new_test_expected_json_str.strip() else {}
                        except json.JSONDecodeError:
                            st.error("Invalid JSON in 'Expected JSON' for new test. Test not added.")
                            new_test_entry = None # Prevent adding
                    
                    if new_test_entry:
                        tests.append(new_test_entry)
                        tests.sort(key=lambda x: x.get('level', 0)) # Keep sorted by level
                        st.rerun()
                else:
                    st.warning("Prompt cannot be empty for a new test.")
        st.markdown("---")

    if st.sidebar.button("💾 Save All Changes to gauntlet.json", use_container_width=True, type="primary"):
        save_gauntlet_data(data)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Preview gauntlet.json")
    st.sidebar.json(data)

if __name__ == "__main__":
    main()
