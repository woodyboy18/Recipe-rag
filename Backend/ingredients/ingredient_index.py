import os
import pickle
from typing import List, Dict, Set, Union, Any
from ingredients.normalizer import normalize_ingredient, normalize_ingredient_list

class IngredientIndex:
    """
    Inverted index mapping canonical ingredient names to sets of recipe IDs.
    Enables instant set intersection candidate filtering for multi-ingredient constraints.
    """
    def __init__(self):
        self.index: Dict[str, Set[Any]] = {}
        self.recipe_ingredients: Dict[Any, Set[str]] = {}

    def build_from_recipes(self, recipes: List[Dict[str, Any]]):
        """
        Builds inverted index from a list of recipe dicts or metadata rows.
        """
        self.index.clear()
        self.recipe_ingredients.clear()

        for idx, recipe in enumerate(recipes):
            rec_id = recipe.get("recipe_id", recipe.get("id", idx))

            if "normalized_ingredients" in recipe and isinstance(recipe["normalized_ingredients"], list):
                norm_ings = recipe["normalized_ingredients"]
            else:
                raw_ings = recipe.get("ingredients", [])
                if isinstance(raw_ings, str):
                    raw_ings = [i.strip() for i in raw_ings.split(",") if i.strip()]
                norm_ings = normalize_ingredient_list(raw_ings)

            norm_set = set(norm_ings)
            self.recipe_ingredients[rec_id] = norm_set

            for ing in norm_set:
                if ing not in self.index:
                    self.index[ing] = set()
                self.index[ing].add(rec_id)

    def find_candidate_recipe_ids(
        self,
        required_ingredients: List[str] = None,
        avoided_ingredients: List[str] = None,
        all_recipe_ids: List[Any] = None
    ) -> Set[Any]:
        """
        Returns set of candidate recipe IDs satisfying all required ingredients and excluding all avoided ingredients.
        """
        req_norm = normalize_ingredient_list(required_ingredients or [])
        avoid_norm = normalize_ingredient_list(avoided_ingredients or [])

        # Start with all recipe IDs if no required ingredients specified
        if not req_norm:
            if all_recipe_ids is not None:
                candidate_ids = set(all_recipe_ids)
            else:
                candidate_ids = set(self.recipe_ingredients.keys())
        else:
            # Intersection of all required ingredient sets
            sets_to_intersect = []
            for ing in req_norm:
                if ing in self.index:
                    sets_to_intersect.append(self.index[ing])
                else:
                    # Check if splitting ing into sub-tokens yields any known ingredients in self.index
                    sub_tokens = [t for t in ing.split() if t in self.index]
                    if sub_tokens:
                        for st in sub_tokens:
                            sets_to_intersect.append(self.index[st])

            if sets_to_intersect:
                candidate_ids = set.intersection(*sets_to_intersect)
            else:
                candidate_ids = set(all_recipe_ids) if all_recipe_ids is not None else set(self.recipe_ingredients.keys())

        # Remove candidates containing any avoided ingredient
        if avoid_norm and candidate_ids:
            for avoid_ing in avoid_norm:
                if avoid_ing in self.index:
                    candidate_ids -= self.index[avoid_ing]

        return candidate_ids

    def save(self, file_path: str):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            pickle.dump({"index": self.index, "recipe_ingredients": self.recipe_ingredients}, f)

    @classmethod
    def load(cls, file_path: str) -> "IngredientIndex":
        instance = cls()
        with open(file_path, "rb") as f:
            data = pickle.load(f)
            instance.index = data.get("index", {})
            instance.recipe_ingredients = data.get("recipe_ingredients", {})
        return instance
