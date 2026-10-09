import sys
import os

sys.path.insert(0, 'Backend')
from core.recipe_engine import answer_query

print("=== CALLING answer_query('give me recipes using asafoetida', mode='find') ===")
res1 = answer_query("give me recipes using asafoetida", requested_mode="find")
print("Mode:", res1.get("mode"))
print("Title:", res1.get("title"))
print("Required ings:", res1.get("required_ingredients"))
print("Retrieved count:", len(res1.get("retrieved_recipes", [])))
for r in res1.get("retrieved_recipes", []):
    print("   Doc:", r.get("title"))

print("\n=== CALLING answer_query('asafoetida', mode='find') ===")
res2 = answer_query("asafoetida", requested_mode="find")
print("Mode:", res2.get("mode"))
print("Title:", res2.get("title"))
print("Required ings:", res2.get("required_ingredients"))
print("Retrieved count:", len(res2.get("retrieved_recipes", [])))
for r in res2.get("retrieved_recipes", []):
    print("   Doc:", r.get("title"))

print("\n=== CALLING answer_query('create a new recipe using asafoetida', mode='novel') ===")
res3 = answer_query("create a new recipe using asafoetida", requested_mode="novel")
print("Mode:", res3.get("mode"))
print("Title:", res3.get("title"))
print("Ingredients:", [i.get('name') if isinstance(i, dict) else i for i in res3.get("ingredients", [])])
print("Instructions:")
for st in res3.get("instructions", []):
    if isinstance(st, dict):
        print(f"  Step {st.get('step')}: {st.get('text')}")
