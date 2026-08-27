import unittest
from constraints.constraint_extractor import parse_query_to_spec

class TestConstraintExtractor(unittest.TestCase):
    def test_query_strawberry_and_milk_find(self):
        q = "show me recipe with strawberry and milk"
        spec = parse_query_to_spec(q)
        self.assertEqual(spec.mode, "find")
        self.assertIn("strawberry", spec.ingredients_to_include)
        self.assertIn("milk", spec.ingredients_to_include)
        self.assertEqual(spec.ingredients_to_avoid, [])

    def test_query_novel_dessert_without_eggs(self):
        q = "create a new dessert with strawberry and milk but no eggs"
        spec = parse_query_to_spec(q)
        self.assertEqual(spec.mode, "novel")
        self.assertEqual(spec.meal, "dessert")
        self.assertIn("strawberry", spec.ingredients_to_include)
        self.assertIn("milk", spec.ingredients_to_include)
        self.assertIn("egg", spec.ingredients_to_avoid)

    def test_conjunction_avoidance_splitting(self):
        q = "high protein breakfast without eggs and milk"
        spec = parse_query_to_spec(q)
        self.assertIn("egg", spec.ingredients_to_avoid)
        self.assertIn("milk", spec.ingredients_to_avoid)
        self.assertNotIn("eggs and milk", spec.ingredients_to_avoid)

if __name__ == "__main__":
    unittest.main()
