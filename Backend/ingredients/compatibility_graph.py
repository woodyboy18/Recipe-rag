import os
import math
import pickle
from typing import List, Dict, Tuple, Set, Any
from ingredients.normalizer import normalize_ingredient, normalize_ingredient_list

class IngredientCompatibilityGraph:
    """
    Data-driven ingredient co-occurrence & Positive PMI (PPMI) graph.
    Computes pairwise compatibility between canonical ingredients based on dataset co-occurrences.
    """
    def __init__(self):
        self.ingredient_counts: Dict[str, int] = {}
        self.co_occurrence_counts: Dict[Tuple[str, str], int] = {}
        self.pmi_scores: Dict[Tuple[str, str], float] = {}
        self.total_recipes: int = 0

    def build_from_recipes(self, recipes: List[Dict[str, Any]]):
        """
        Builds graph nodes and co-occurrence edges from recipe dataset.
        """
        self.ingredient_counts.clear()
        self.co_occurrence_counts.clear()
        self.pmi_scores.clear()
        self.total_recipes = len(recipes)

        for recipe in recipes:
            if "normalized_ingredients" in recipe and isinstance(recipe["normalized_ingredients"], list):
                norm_ings = recipe["normalized_ingredients"]
            else:
                raw_ings = recipe.get("ingredients", [])
                if isinstance(raw_ings, str):
                    raw_ings = [i.strip() for i in raw_ings.split(",") if i.strip()]
                norm_ings = normalize_ingredient_list(raw_ings)

            unique_ings = list(set(norm_ings))

            for ing in unique_ings:
                self.ingredient_counts[ing] = self.ingredient_counts.get(ing, 0) + 1

            for i in range(len(unique_ings)):
                for j in range(i + 1, len(unique_ings)):
                    pair = tuple(sorted([unique_ings[i], unique_ings[j]]))
                    self.co_occurrence_counts[pair] = self.co_occurrence_counts.get(pair, 0) + 1

        # Compute Positive PMI
        if self.total_recipes > 0:
            for (ing1, ing2), co_count in self.co_occurrence_counts.items():
                p_xy = co_count / self.total_recipes
                p_x = self.ingredient_counts[ing1] / self.total_recipes
                p_y = self.ingredient_counts[ing2] / self.total_recipes

                if p_x > 0 and p_y > 0:
                    pmi = math.log2(p_xy / (p_x * p_y))
                    self.pmi_scores[(ing1, ing2)] = max(0.0, pmi)  # Positive PMI

    def compatibility_score(self, ing1: str, ing2: str) -> float:
        norm1 = normalize_ingredient(ing1)
        norm2 = normalize_ingredient(ing2)

        if not norm1 or not norm2 or norm1 == norm2:
            return 1.0

        pair = tuple(sorted([norm1, norm2]))
        if pair in self.pmi_scores:
            return float(self.pmi_scores[pair])

        # Raw co-occurrence fallback
        co_count = self.co_occurrence_counts.get(pair, 0)
        if co_count > 0:
            return min(1.0, co_count / 10.0)

        return 0.0

    def get_compatible(self, ingredient: str, top_n: int = 10) -> List[Tuple[str, float]]:
        norm = normalize_ingredient(ingredient)
        if not norm:
            return []

        candidates = []
        for (ing1, ing2), score in self.pmi_scores.items():
            if ing1 == norm:
                candidates.append((ing2, score))
            elif ing2 == norm:
                candidates.append((ing1, score))

        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:top_n]

    def recipe_compatibility_score(self, ingredients: List[str]) -> float:
        norm_ings = normalize_ingredient_list(ingredients)
        if len(norm_ings) <= 1:
            return 1.0

        scores = []
        for i in range(len(norm_ings)):
            for j in range(i + 1, len(norm_ings)):
                s = self.compatibility_score(norm_ings[i], norm_ings[j])
                scores.append(s)

        if not scores:
            return 0.5

        # Return average pairwise PPMI normalized
        avg_score = sum(scores) / len(scores)
        return round(min(1.0, avg_score / 3.0), 3)

    def save(self, file_path: str):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            pickle.dump({
                "ingredient_counts": self.ingredient_counts,
                "co_occurrence_counts": self.co_occurrence_counts,
                "pmi_scores": self.pmi_scores,
                "total_recipes": self.total_recipes
            }, f)

    @classmethod
    def load(cls, file_path: str) -> "IngredientCompatibilityGraph":
        graph = cls()
        with open(file_path, "rb") as f:
            data = pickle.load(f)
            graph.ingredient_counts = data.get("ingredient_counts", {})
            graph.co_occurrence_counts = data.get("co_occurrence_counts", {})
            graph.pmi_scores = data.get("pmi_scores", {})
            graph.total_recipes = data.get("total_recipes", 0)
        return graph
