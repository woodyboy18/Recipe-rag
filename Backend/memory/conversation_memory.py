import json
import os

# ================= CONFIG =================
MEMORY_DIR = "memory"
MEMORY_FILE = os.path.join(MEMORY_DIR, "user_memory.json")


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
        return json.load(f)


# ================= SAVE =================
def save_turn(user_query, assistant_response, constraints):
    """
    Save one user-assistant conversation turn.
    """

    history = load_history()

    history.append(
        {
            "user": user_query,
            "assistant": assistant_response,
            "constraints": constraints
        }
    )

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)


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
