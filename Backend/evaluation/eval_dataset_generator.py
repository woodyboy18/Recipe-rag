"""
Novel Recipe Evaluation Dataset Generator
Runs a benchmark suite of 10-15 novel synthesis queries through the existing RecipeFusion engine,
capturing the complete evaluation triplet:
  (User Query, Retrieved Parent Recipes, Generated Novel Recipe)
Saves the records into:
  1. Backend/memory/eval_novel_recipes.json (Primary evaluation dataset)
  2. Backend/memory/user_memory.json (Conversation memory)
"""

import os
import sys
import json
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.recipe_engine import answer_query
from memory.conversation_memory import save_turn

# 15 Diverse Benchmark Queries for Novel Recipe Synthesis
BENCHMARK_NOVEL_QUERIES = [
    {
        "id": "novel_01",
        "query": "create a new high-protein vegetarian breakfast under 20 minutes without eggs",
        "category": "Dietary exclusion + High protein"
    },
    {
        "id": "novel_02",
        "query": "innovative vegan dinner combining chickpeas and spinach with no garlic",
        "category": "Vegan + Exclusion"
    },
    {
        "id": "novel_03",
        "query": "invent a unique low-carb skillet dish using paneer and broccoli",
        "category": "Low-carb + Pairing"
    },
    {
        "id": "novel_04",
        "query": "make a novel dessert with strawberry and oats without refined sugar",
        "category": "Dessert + Health constraint"
    },
    {
        "id": "novel_05",
        "query": "create a fusion dinner using tofu and peanut sauce without soy sauce",
        "category": "Fusion + Allergen exclusion"
    },
    {
        "id": "novel_06",
        "query": "create a healthy lunch bowl with lentils and sweet potato under 30 minutes",
        "category": "Time limit + Legume"
    },
    {
        "id": "novel_07",
        "query": "invent a savory breakfast dish combining avocado and mushrooms with no dairy",
        "category": "Dairy-free breakfast"
    },
    {
        "id": "novel_08",
        "query": "create a new recipe for chicken and quinoa without tomatoes",
        "category": "Poultry + Nightshade-free"
    },
    {
        "id": "novel_09",
        "query": "synthesize a creative dinner featuring salmon and asparagus with lemon butter",
        "category": "Seafood + Technique"
    },
    {
        "id": "novel_10",
        "query": "invent an Indian-Mediterranean fusion appetizer using paneer and olives",
        "category": "Cross-cuisine fusion"
    },
    {
        "id": "novel_11",
        "query": "create a quick 15-minute high-energy afternoon snack with dates and almonds",
        "category": "Quick snack + Energy"
    },
    {
        "id": "novel_12",
        "query": "synthesize a gluten-free vegetarian pasta substitute using zucchini and walnuts",
        "category": "Gluten-free + Vegetarian"
    },
    {
        "id": "novel_13",
        "query": "invent a spicy comforting winter soup using black beans and corn without onion",
        "category": "Soup + Allium-free"
    },
    {
        "id": "novel_14",
        "query": "create a novel dessert pairing mango and coconut milk with no gelatin",
        "category": "Vegan dessert + Tropical"
    },
    {
        "id": "novel_15",
        "query": "synthesize a creative high-fiber lunch using cauliflower rice and bell peppers",
        "category": "Keto/Fiber lunch"
    }
]

EVAL_OUTPUT_PATH = os.path.join(PROJECT_ROOT, "memory", "eval_novel_recipes.json")


def generate_benchmark_recipes(num_recipes: int = 15, novelty_level: str = "balanced") -> str:
    """
    Executes novel recipe generation across benchmark queries and persists full triplets.
    """
    os.makedirs(os.path.dirname(EVAL_OUTPUT_PATH), exist_ok=True)
    selected_queries = BENCHMARK_NOVEL_QUERIES[:num_recipes]
    
    print(f"\n{'='*70}")
    print(f"RECIPEFUSION NOVEL RECIPE DATASET GENERATOR")
    print(f"Generating {len(selected_queries)} novel recipes for LLM-as-a-Judge evaluation...")
    print(f"{'='*70}\n")

    eval_records = []

    for idx, item in enumerate(selected_queries, 1):
        q_id = item["id"]
        q_text = item["query"]
        category = item["category"]

        print(f"[{idx}/{len(selected_queries)}] Processing ({q_id}): \"{q_text}\"")
        start_time = time.time()

        try:
            result = answer_query(q_text, requested_mode="novel", novelty_level=novelty_level)
            elapsed = time.time() - start_time

            recipe_payload = {
                "title": result.get("title", "Untitled Novel Recipe"),
                "ingredients": result.get("ingredients", []),
                "instructions": result.get("instructions", []),
                "servings": result.get("servings", 2),
                "prep_time": result.get("prep_time", 10),
                "cook_time": result.get("cook_time", 15),
                "mode": result.get("mode", "synthesized")
            }

            retrieved = result.get("retrieved_recipes", [])
            constraints = result.get("constraints", {})

            eval_record = {
                "id": q_id,
                "user_query": q_text,
                "category": category,
                "constraints": constraints,
                "retrieved_recipes": retrieved,
                "generated_recipe": recipe_payload,
                "generation_time_sec": round(elapsed, 2),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }

            eval_records.append(eval_record)

            # Also update user_memory.json via conversation memory
            assistant_summary = f"{recipe_payload['title']} (synthesized)"
            save_turn(
                user_query=q_text,
                assistant_response=assistant_summary,
                constraints=str(constraints),
                recipe_details=recipe_payload,
                retrieved_recipes=retrieved
            )

            print(f"  -> Generated: \"{recipe_payload['title']}\" ({len(recipe_payload['ingredients'])} ings, {len(recipe_payload['instructions'])} steps)")
            print(f"  -> Retrieved Parents: {len(retrieved)} recipes | Latency: {round(elapsed, 2)}s\n")

        except Exception as e:
            print(f"  -> ERROR generating recipe for query '{q_text}': {e}\n")

    # Save to eval_novel_recipes.json
    with open(EVAL_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(eval_records, f, indent=4)

    print(f"{'='*70}")
    print(f"SUCCESS: Generated {len(eval_records)} novel recipes.")
    print(f"Saved evaluation dataset to: {EVAL_OUTPUT_PATH}")
    print(f"Saved conversation history to: {os.path.join(PROJECT_ROOT, 'memory', 'user_memory.json')}")
    print(f"{'='*70}\n")
    return EVAL_OUTPUT_PATH


if __name__ == "__main__":
    n = 15
    if len(sys.argv) > 1:
        try:
            n = int(sys.argv[1])
        except ValueError:
            pass
    generate_benchmark_recipes(num_recipes=n)
