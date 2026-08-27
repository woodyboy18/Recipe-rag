"""
Structured Memory Manager Module
Persists structured user profiles (allergies, dietary preferences, favorite cuisines),
active recipe state, and chronological conversation turns.
"""

import os
import json
from state.recipe_state import RecipeState
from state.recipe_version_manager import RecipeVersionManager

MEMORY_FILE_PATH = os.path.join(os.path.dirname(__file__), "structured_memory.json")

class UserPreferences:
    def __init__(
        self,
        dietary_preference: str = None, # vegetarian, vegan, keto, low carb, gluten free
        allergies: list = None,
        disliked_ingredients: list = None,
        favorite_cuisines: list = None,
        high_protein_preference: bool = False
    ):
        self.dietary_preference = dietary_preference
        self.allergies = allergies or []
        self.disliked_ingredients = disliked_ingredients or []
        self.favorite_cuisines = favorite_cuisines or []
        self.high_protein_preference = high_protein_preference

    def to_dict(self) -> dict:
        return {
            "dietary_preference": self.dietary_preference,
            "allergies": self.allergies,
            "disliked_ingredients": self.disliked_ingredients,
            "favorite_cuisines": self.favorite_cuisines,
            "high_protein_preference": self.high_protein_preference
        }

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            dietary_preference=d.get("dietary_preference"),
            allergies=d.get("allergies", []),
            disliked_ingredients=d.get("disliked_ingredients", []),
            favorite_cuisines=d.get("favorite_cuisines", []),
            high_protein_preference=d.get("high_protein_preference", False)
        )


class ConversationMemoryManager:
    def __init__(self, memory_file: str = MEMORY_FILE_PATH):
        self.memory_file = memory_file
        self.user_preferences = UserPreferences()
        self.active_recipe_state = None
        self.version_manager = RecipeVersionManager()
        self.turns = []
        self.last_intent = "UNKNOWN"
        self.load_memory()

    def reset_session(self):
        """Reset active session state while preserving preferences."""
        self.active_recipe_state = None
        self.version_manager = RecipeVersionManager()
        self.turns = []
        self.last_intent = "UNKNOWN"
        self.save_memory()

    def set_active_recipe(self, recipe_state: RecipeState):
        self.active_recipe_state = recipe_state
        self.version_manager.add_version(recipe_state)
        self.save_memory()

    def update_active_recipe(self, recipe_state: RecipeState):
        self.active_recipe_state = recipe_state
        self.version_manager.add_version(recipe_state)
        self.save_memory()

    def undo_recipe_state(self) -> RecipeState:
        state = self.version_manager.undo()
        if state:
            self.active_recipe_state = state
            self.save_memory()
        return self.active_recipe_state

    def redo_recipe_state(self) -> RecipeState:
        state = self.version_manager.redo()
        if state:
            self.active_recipe_state = state
            self.save_memory()
        return self.active_recipe_state

    def add_turn(self, user_text: str, assistant_summary: str, intent: str, recipe_state: RecipeState = None):
        self.last_intent = intent
        if recipe_state:
            self.set_active_recipe(recipe_state)

        turn_obj = {
            "user": user_text,
            "assistant": assistant_summary,
            "intent": intent,
            "recipe_id": self.active_recipe_state.id if self.active_recipe_state else None,
            "recipe_title": self.active_recipe_state.title if self.active_recipe_state else None,
            "version": self.active_recipe_state.version if self.active_recipe_state else 1
        }
        self.turns.append(turn_obj)
        self.save_memory()

    def get_recent_conversation_summary(self, n: int = 5) -> str:
        recent = self.turns[-n:]
        summary_lines = []
        for t in recent:
            summary_lines.append(f"User: {t['user']}")
            if t.get("assistant"):
                summary_lines.append(f"Assistant: {t['assistant']}")
        return "\n".join(summary_lines)

    def save_memory(self):
        try:
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            data = {
                "user_preferences": self.user_preferences.to_dict(),
                "last_intent": self.last_intent,
                "active_recipe": self.active_recipe_state.to_dict() if self.active_recipe_state else None,
                "version_history": [s.to_dict() for s in self.version_manager.history],
                "version_index": self.version_manager.current_index,
                "turns": self.turns[-20:]
            }
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Memory save warning: {e}")

    def load_memory(self):
        if not os.path.exists(self.memory_file):
            return
        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "user_preferences" in data:
                self.user_preferences = UserPreferences.from_dict(data["user_preferences"])
            if "last_intent" in data:
                self.last_intent = data["last_intent"]
            if data.get("active_recipe"):
                self.active_recipe_state = RecipeState.from_dict(data["active_recipe"])
            if data.get("version_history"):
                self.version_manager.history = [RecipeState.from_dict(v) for v in data["version_history"]]
                self.version_manager.current_index = data.get("version_index", len(self.version_manager.history) - 1)
            if "turns" in data:
                self.turns = data["turns"]
        except Exception as e:
            print(f"Memory load warning: {e}")
