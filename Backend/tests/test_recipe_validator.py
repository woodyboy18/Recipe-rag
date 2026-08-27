import unittest
from core.schemas import QuerySpec
from validation.recipe_validator import validate_synthesized_recipe

class TestRecipeValidator(unittest.TestCase):
    def test_validator_hard_failures(self):
        spec = QuerySpec(
            original_query="strawberry milk dessert",
            ingredients_to_include=["strawberry", "milk"],
            ingredients_to_avoid=["egg"]
        )

        # Missing required ingredient 'milk'
        invalid_rec = {
            "title": "Strawberry Pudding",
            "ingredients": ["1 cup strawberry", "1 tbsp sugar"],
            "instructions": ["Blend strawberry with sugar."]
        }
        res = validate_synthesized_recipe(invalid_rec, spec)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("Missing mandatory required ingredients" in e for e in res.errors))

        # Contains avoided ingredient 'egg'
        invalid_rec2 = {
            "title": "Egg Strawberry Pudding",
            "ingredients": ["1 cup strawberry", "1 cup milk", "1 egg"],
            "instructions": ["Mix strawberry, milk and egg.", "Bake."]
        }
        res2 = validate_synthesized_recipe(invalid_rec2, spec)
        self.assertFalse(res2.is_valid)
        self.assertTrue(any("Contains forbidden ingredients" in e for e in res2.errors))

    def test_validator_valid_recipe(self):
        spec = QuerySpec(
            original_query="strawberry milk dessert",
            ingredients_to_include=["strawberry", "milk"],
            ingredients_to_avoid=["egg"]
        )

        valid_rec = {
            "title": "Strawberry Milk Gelato",
            "ingredients": ["1 cup strawberry", "1 cup milk", "2 tbsp honey"],
            "instructions": ["Blend strawberry, milk, and honey until smooth.", "Chill and serve."]
        }
        res = validate_synthesized_recipe(valid_rec, spec)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.constraint_score, 1.0)

if __name__ == "__main__":
    unittest.main()
