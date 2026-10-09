import unittest
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ingredients.ontology import IngredientOntology
from substitution.ingredient_substitution import find_substitutes

class TestIngredientOntology(unittest.TestCase):

    def setUp(self):
        self.ontology = IngredientOntology()

    def test_ontology_lookup(self):
        egg_info = self.ontology.get_ingredient_info("egg")
        self.assertIsNotNone(egg_info)
        self.assertEqual(egg_info.category, "animal_protein")
        self.assertIn("binder", egg_info.culinary_roles)

    def test_ontology_substitutions(self):
        subs = self.ontology.find_ontology_substitutes("egg", diet_preference="vegetarian")
        self.assertGreaterThan(len(subs), 0) if hasattr(self, 'assertGreaterThan') else self.assertTrue(len(subs) > 0)
        sub_names = [s["substitute"].lower() for s in subs]
        self.assertTrue("tofu" in sub_names or "mashed banana" in sub_names)
        self.assertNotEqual(subs[0]["culinary_role"], "")

    def test_butter_substitution(self):
        subs = self.ontology.find_ontology_substitutes("butter")
        self.assertTrue(len(subs) > 0)
        sub_names = [s["substitute"].lower() for s in subs]
        self.assertTrue("olive oil" in sub_names or "ghee" in sub_names)

    def test_find_substitutes_engine(self):
        subs = find_substitutes("chicken", diet_preference="vegetarian")
        self.assertTrue(len(subs) > 0)
        sub_names = [s["substitute"].lower() for s in subs]
        self.assertTrue("soya chunks" in sub_names or "paneer" in sub_names or "tofu" in sub_names)

if __name__ == "__main__":
    unittest.main()
