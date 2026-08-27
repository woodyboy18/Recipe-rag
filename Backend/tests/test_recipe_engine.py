import unittest
from unittest.mock import patch
from core.recipe_engine import answer_query

class TestRecipeEngine(unittest.TestCase):
    def test_engine_find_existing_recipe(self):
        res = answer_query("show me recipe with strawberry and milk", requested_mode="find")
        self.assertEqual(res["mode"], "retrieved")
        self.assertIn("recipe", res)
        self.assertNotEqual(res["recipe"]["title"], "")
        self.assertEqual(res["scores"]["constraint_satisfaction"], 1.0)

    def test_engine_novel_recipe_synthesis(self):
        mock_ollama_json = '''{
            "title": "Grounded Strawberry Milk Delight",
            "servings": 2,
            "prep_time": 10,
            "cook_time": 0,
            "ingredients": [
                {"name": "strawberry", "amount": "1", "unit": "cup", "role": "flavor", "supported_by": [1]},
                {"name": "milk", "amount": "1", "unit": "cup", "role": "base", "supported_by": [1]},
                {"name": "honey", "amount": "1", "unit": "tbsp", "role": "sweetener", "supported_by": [1]}
            ],
            "instructions": [
                {"step": 1, "text": "Blend fresh strawberry, milk, and honey until smooth.", "supported_by": [1]},
                {"step": 2, "text": "Chill in the refrigerator for 10 minutes and serve.", "supported_by": [1]}
            ]
        }'''

        with patch("generation.novel_generator.call_ollama_raw", return_value=mock_ollama_json):
            res = answer_query("create a new dessert with strawberry and milk but no eggs", requested_mode="novel")
            self.assertEqual(res["mode"], "synthesized")
            self.assertEqual(res["recipe"]["title"], "Grounded Strawberry Milk Delight")
            self.assertIn("provenance", res)
            self.assertEqual(res["scores"]["constraint_satisfaction"], 1.0)
            self.assertIn("novelty", res["scores"])

if __name__ == "__main__":
    unittest.main()
