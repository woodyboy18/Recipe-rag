"""
Recipe Version Manager Module
Manages state snapshot history, undo, redo, and version diff comparisons.
"""

import copy
from state.recipe_state import RecipeState

class RecipeVersionManager:
    def __init__(self, initial_state: RecipeState = None):
        self.history = []  # List of RecipeState snapshots
        self.current_index = -1

        if initial_state:
            self.add_version(initial_state)

    def add_version(self, state: RecipeState):
        """Add a new version state to history tree, truncating redo branch."""
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]

        state_copy = copy.deepcopy(state)
        state_copy.version = len(self.history) + 1
        self.history.append(state_copy)
        self.current_index = len(self.history) - 1
        return state_copy

    def get_current_version(self) -> RecipeState:
        if self.current_index >= 0 and self.current_index < len(self.history):
            return self.history[self.current_index]
        return None

    def undo(self) -> RecipeState:
        if self.can_undo():
            self.current_index -= 1
            return self.history[self.current_index]
        return self.get_current_version()

    def redo(self) -> RecipeState:
        if self.can_redo():
            self.current_index += 1
            return self.history[self.current_index]
        return self.get_current_version()

    def can_undo(self) -> bool:
        return self.current_index > 0

    def can_redo(self) -> bool:
        return self.current_index < len(self.history) - 1

    def get_version_info(self) -> dict:
        return {
            "current_version": self.current_index + 1,
            "total_versions": len(self.history),
            "can_undo": self.can_undo(),
            "can_redo": self.can_redo()
        }

    def compare_versions(self, version_a_idx: int, version_b_idx: int) -> dict:
        """Compare two version states and return ingredient/instruction diffs."""
        if version_a_idx < 0 or version_a_idx >= len(self.history):
            return {"error": "Invalid version A"}
        if version_b_idx < 0 or version_b_idx >= len(self.history):
            return {"error": "Invalid version B"}

        state_a = self.history[version_a_idx]
        state_b = self.history[version_b_idx]

        ing_a = {ing.name.lower(): ing for ing in state_a.ingredients}
        ing_b = {ing.name.lower(): ing for ing in state_b.ingredients}

        added_ingredients = [ing.name for k, ing in ing_b.items() if k not in ing_a]
        removed_ingredients = [ing.name for k, ing in ing_a.items() if k not in ing_b]

        return {
            "version_a": state_a.version,
            "version_b": state_b.version,
            "added_ingredients": added_ingredients,
            "removed_ingredients": removed_ingredients,
            "servings_change": f"{state_a.servings} -> {state_b.servings}"
        }
