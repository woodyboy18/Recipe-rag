import sys
import os

sys.path.insert(0, 'Backend')
import core.recipe_engine as recipe_engine

recipe_engine.initialize_engine()

def test_query(q, mode='auto'):
    print(f"\n==================================================")
    print(f"QUERY: '{q}' | REQUESTED MODE: {mode}")
    print(f"==================================================")
    res = recipe_engine.answer_query(q, requested_mode=mode)
    print("Effective Mode:", res.get("mode"))
    print("Title:", res.get("title"))
    print("Required Ingredients Spec:", res.get("required_ingredients"))
    print("Avoided Ingredients Spec:", res.get("avoided_ingredients"))
    
    ret_recs = res.get("retrieved_recipes", [])
    print(f"Retrieved Recipes Count: {len(ret_recs)}")
    for i, r in enumerate(ret_recs[:5], 1):
        print(f"   {i}. {r.get('title')} (score={r.get('rrf_score')})")

if __name__ == "__main__":
    test_query("paneer butter masala", "auto")
    test_query("show me a recipe for paneer butter masala", "find")
    test_query("chicken biryani", "find")
    test_query("show me a recipe for chicken biryani", "find")
    test_query("give me recipes using asafoetida", "find")
    test_query("asafoetida", "find")
    test_query("dal with hing and cumin", "find")
    test_query("create a new recipe for chicken and paneer", "novel")
