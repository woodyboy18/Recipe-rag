import os
import sys
import json
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.recipe_engine import answer_query

EVAL_QUERIES_PATH = os.path.join(os.path.dirname(__file__), "novel_test_queries.json")

def evaluate_novelty_suite():
    """
    Evaluates grounded novel recipe synthesis pipeline across:
    - Constraint satisfaction rate
    - Grounding coverage
    - Ingredient-step consistency
    - Compatibility score
    - Novelty score
    - Latency (seconds)
    """
    if not os.path.exists(EVAL_QUERIES_PATH):
        print(f"Evaluation query file missing at: {EVAL_QUERIES_PATH}")
        return

    with open(EVAL_QUERIES_PATH, "r", encoding="utf-8") as f:
        queries = json.load(f)

    results = []
    print("Starting Novelty Evaluation Suite...\n")

    for item in queries:
        q_text = item["query"]
        mode = item.get("mode", "auto")
        
        start_t = time.time()
        res = answer_query(q_text, requested_mode=mode)
        latency = time.time() - start_t

        scores = res.get("scores", {})

        eval_row = {
            "query": q_text,
            "requested_mode": mode,
            "resulting_mode": res.get("mode"),
            "title": res.get("recipe", {}).get("title"),
            "constraint_satisfaction": scores.get("constraint_satisfaction", 0.0),
            "grounding": scores.get("grounding", 0.0),
            "consistency": scores.get("ingredient_step_consistency", 0.0),
            "compatibility": scores.get("compatibility", 0.0),
            "novelty": scores.get("novelty", 0.0),
            "latency_sec": round(latency, 2)
        }
        results.append(eval_row)

        print(f"Query: {q_text}")
        print(f"  Mode: {eval_row['resulting_mode']} | Title: {eval_row['title']}")
        print(f"  Scores -> Constraint: {eval_row['constraint_satisfaction']}, Grounding: {eval_row['grounding']}, Novelty: {eval_row['novelty']}, Latency: {eval_row['latency_sec']}s\n")

    avg_constraint = sum(r["constraint_satisfaction"] for r in results) / len(results) if results else 0
    avg_grounding = sum(r["grounding"] for r in results) / len(results) if results else 0
    avg_novelty = sum(r["novelty"] for r in results) / len(results) if results else 0

    print("=" * 50)
    print("EVALUATION SUMMARY")
    print(f"Total Queries Evaluated: {len(results)}")
    print(f"Average Constraint Satisfaction: {round(avg_constraint, 3)}")
    print(f"Average Grounding Coverage: {round(avg_grounding, 3)}")
    print(f"Average Novelty Score: {round(avg_novelty, 3)}")
    print("=" * 50)

if __name__ == "__main__":
    evaluate_novelty_suite()
