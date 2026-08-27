import json
import os
import unittest
from ingredients.ingredient_index import IngredientIndex

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "recipes_small.json")

class TestIngredientIndex(unittest.TestCase):
    def test_ingredient_index_intersection(self):
        with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
            recipes = json.load(f)

        idx = IngredientIndex()
        idx.build_from_recipes(recipes)

        # Intersection of strawberry AND milk
        candidates = idx.find_candidate_recipe_ids(
            required_ingredients=["strawberry", "milk"],
            avoided_ingredients=[]
        )
        # Recipe 1 (Strawberry Smoothie) contains strawberry and milk
        self.assertIn(1, candidates)

    def test_ingredient_index_avoidance(self):
        with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
            recipes = json.load(f)

        idx = IngredientIndex()
        idx.build_from_recipes(recipes)

        # Strawberry AND milk BUT avoid egg
        candidates = idx.find_candidate_recipe_ids(
            required_ingredients=["strawberry", "milk"],
            avoided_ingredients=["egg"]
        )
        self.assertIn(1, candidates)
        self.assertNotIn(4, candidates)  # Recipe 4 has egg

if __name__ == "__main__":
    unittest.main()
