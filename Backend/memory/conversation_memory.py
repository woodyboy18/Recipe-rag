import json
import os
from datetime import datetime

# ================= CONFIG =================
MEMORY_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(MEMORY_DIR, "user_memory.json")
EVAL_FILE = os.path.join(MEMORY_DIR, "eval_novel_recipes.json")


# ================= INITIALIZE =================
def initialize_memory():
    """
    Create the memory folder and JSON file if they do not exist.
    """
    os.makedirs(MEMORY_DIR, exist_ok=True)

    if not os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)


# ================= LOAD =================
def load_history():
    """
    Load the complete conversation history.
    """
    initialize_memory()

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []


# ================= SAVE =================
def save_turn(user_query, assistant_response, constraints, recipe_details=None, retrieved_recipes=None):
    """
    Save one user-assistant conversation turn.
    Optionally stores full recipe details and retrieved parent recipes to enable
    comprehensive downstream LLM-as-a-Judge evaluation.
    """
    history = load_history()

    turn_data = {
        "user": user_query,
        "assistant": assistant_response,
        "constraints": constraints
    }

    if recipe_details:
        turn_data["recipe_details"] = recipe_details
    if retrieved_recipes:
        turn_data["retrieved_recipes"] = retrieved_recipes

    history.append(turn_data)

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

    # If full recipe details exist (e.g. synthesized novel recipe), also save to eval_novel_recipes.json
    if recipe_details:
        _save_novel_eval_record(user_query, constraints, recipe_details, retrieved_recipes)


def _save_novel_eval_record(user_query, constraints, recipe_details, retrieved_recipes):
    """
    Maintains a dedicated evaluation dataset file containing full novel recipe triplets.
    """
    try:
        records = []
        if os.path.exists(EVAL_FILE):
            with open(EVAL_FILE, "r", encoding="utf-8") as f:
                try:
                    records = json.load(f)
                except Exception:
                    records = []

        record = {
            "id": f"rec_eval_{len(records) + 1:03d}",
            "user_query": user_query,
            "constraints": constraints,
            "retrieved_recipes": retrieved_recipes or [],
            "generated_recipe": recipe_details,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        records.append(record)

        with open(EVAL_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=4)
    except Exception as e:
        print(f"Warning: Failed to save to eval_novel_recipes.json: {e}")


# ================= RECENT HISTORY =================
def get_recent_history(last_n=5):
    """
    Return the most recent N conversation turns.
    """
    history = load_history()

    if len(history) <= last_n:
        return history

    return history[-last_n:]


# ================= CLEAR =================
def clear_history():
    """
    Delete all conversation history.
    """
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=4)


# ================= FORMAT HISTORY =================
def format_history(last_n=5):
    """
    Convert conversation history into a prompt-friendly string.
    """
    history = get_recent_history(last_n)

    if not history:
        return "No previous conversation."

    formatted = []

    for turn in history:
        formatted.append(f"User: {turn['user']}")
        formatted.append(f"Assistant: {turn['assistant']}")
        formatted.append("")

    return "\n".join(formatted)
