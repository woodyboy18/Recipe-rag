"""
Batch Evaluation Orchestrator for RecipeFusion
Evaluates novel recipes using the G-Eval-inspired LLM-as-a-Judge Framework.
Produces:
- Detailed JSONL evaluation records (with CoT reasoning, evidence, issues)
- CSV results table
- LaTeX-formatted academic summary table with Means and Standard Deviations
Strictly restricted to FOUR metrics in [0.0, 1.0]:
  1. Correctness
  2. Faithfulness
  3. Hallucination-Free Score
  4. Constraint Adherence
  Overall Score = (C + F + H + A) / 4
"""

import os
import sys
import json
import csv
import argparse
import math
from datetime import datetime
from typing import List, Dict, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from evaluation.llm_judge import LLMJudge, DEFAULT_VLLM_API_BASE, DEFAULT_JUDGE_MODEL


def load_recipes_for_evaluation(input_path: str) -> List[Dict[str, Any]]:
    """
    Loads recipes from either:
    1. eval_novel_recipes.json (triplets formatted specifically for eval)
    2. user_memory.json (extracts turns containing 'recipe_details')
    3. JSONL file containing recipe triplets
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input evaluation file not found: {input_path}")

    recipes = []
    
    if input_path.endswith(".jsonl"):
        with open(input_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    recipes.append(json.loads(line))
        return recipes

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        for item in data:
            if "generated_recipe" in item and "user_query" in item:
                # Format: eval_novel_recipes.json
                recipes.append(item)
            elif "recipe_details" in item and "user" in item:
                # Format: user_memory.json with enriched recipe_details
                recipes.append({
                    "id": item.get("id", f"turn_{len(recipes)+1:03d}"),
                    "user_query": item["user"],
                    "constraints": item.get("constraints", {}),
                    "retrieved_recipes": item.get("retrieved_recipes", []),
                    "generated_recipe": item["recipe_details"],
                    "timestamp": item.get("timestamp", "")
                })
            elif "title" in item and "ingredients" in item:
                # Standalone raw recipe dict
                recipes.append({
                    "id": f"rec_{len(recipes)+1:03d}",
                    "user_query": item.get("query", item.get("title", "")),
                    "constraints": item.get("constraints", {}),
                    "retrieved_recipes": item.get("retrieved_recipes", []),
                    "generated_recipe": item
                })

    return recipes


def compute_statistics(scores: List[float]) -> Dict[str, float]:
    """Computes mean and sample standard deviation."""
    if not scores:
        return {"mean": 0.0, "std": 0.0}
    n = len(scores)
    mean = sum(scores) / n
    if n <= 1:
        return {"mean": round(mean, 4), "std": 0.0}
    variance = sum((x - mean) ** 2 for x in scores) / (n - 1)
    std = math.sqrt(variance)
    return {"mean": round(mean, 4), "std": round(std, 4)}


def run_batch_evaluation(
    input_file: str,
    output_dir: str,
    model_name: str,
    api_base: str,
    limit: int = None,
    fast_mode: bool = False
):
    """
    Runs evaluation on all recipes in input_file, saves individual evaluations,
    and reports scientific aggregate statistics.
    """
    os.makedirs(output_dir, exist_ok=True)
    all_recipes = load_recipes_for_evaluation(input_file)
    
    if limit and limit > 0:
        all_recipes = all_recipes[:limit]

    print(f"\n{'='*75}")
    print(f"RECIPEFUSION G-EVAL LLM-AS-A-JUDGE BATCH EVALUATOR")
    print(f"Judge Model    : {model_name}")
    print(f"API Base       : {api_base}")
    print(f"Evaluation Mode: {'Unified JSON (Fast)' if fast_mode else 'Strict G-Eval (Sequential with Logprob Expectation)'}")
    print(f"Total Recipes  : {len(all_recipes)}")
    print(f"{'='*75}\n")

    timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    clean_model_tag = model_name.split("/")[-1].replace(":", "_").replace("-", "_")
    output_jsonl = os.path.join(output_dir, f"eval_results_{clean_model_tag}_{timestamp_str}.jsonl")
    output_csv = os.path.join(output_dir, f"eval_results_{clean_model_tag}_{timestamp_str}.csv")

    judge = LLMJudge(
        model_name=model_name,
        api_base=api_base,
        use_strict_logprobs=(not fast_mode)
    )

    results = []
    c_scores, f_scores, h_scores, a_scores, overall_scores = [], [], [], [], []

    for idx, item in enumerate(all_recipes, 1):
        q_id = item.get("id", f"sample_{idx:03d}")
        user_query = item.get("user_query", "")
        retrieved = item.get("retrieved_recipes", [])
        recipe = item.get("generated_recipe", {})
        rec_title = recipe.get("title", "Untitled Recipe") if isinstance(recipe, dict) else str(recipe)[:30]

        print(f"[{idx}/{len(all_recipes)}] Evaluating '{rec_title}' (Query: \"{user_query[:50]}...\")")

        try:
            eval_res = judge.evaluate_recipe(
                user_query=user_query,
                retrieved_recipes=retrieved,
                generated_recipe=recipe,
                fast_mode=fast_mode
            )

            c = eval_res["correctness"]["score"]
            f = eval_res["faithfulness"]["score"]
            h = eval_res["hallucination"]["score"]
            a = eval_res["constraint_adherence"]["score"]
            overall = eval_res["overall_score"]

            c_scores.append(c)
            f_scores.append(f)
            h_scores.append(h)
            a_scores.append(a)
            overall_scores.append(overall)

            print(f"  -> Scores: Correctness={c:.2f} | Faithfulness={f:.2f} | Hallucination-free={h:.2f} | Constraints={a:.2f} => Overall={overall:.4f}")

            record = {
                "id": q_id,
                "user_query": user_query,
                "recipe_title": rec_title,
                "evaluation": eval_res
            }
            results.append(record)

            # Incremental save to JSONL (supports resume on crash)
            with open(output_jsonl, "a", encoding="utf-8") as out_f:
                out_f.write(json.dumps(record) + "\n")

        except Exception as e:
            print(f"  -> ERROR evaluating recipe {q_id}: {e}")

    # Export to CSV
    if results:
        with open(output_csv, "w", newline="", encoding="utf-8") as csv_f:
            writer = csv.writer(csv_f)
            writer.writerow([
                "ID", "Recipe Title", "User Query",
                "Correctness", "Faithfulness", "Hallucination_Free", "Constraint_Adherence",
                "Overall_Score", "Judge_Model", "Timestamp"
            ])
            for r in results:
                ev = r["evaluation"]
                writer.writerow([
                    r["id"],
                    r["recipe_title"],
                    r["user_query"],
                    ev["correctness"]["score"],
                    ev["faithfulness"]["score"],
                    ev["hallucination"]["score"],
                    ev["constraint_adherence"]["score"],
                    ev["overall_score"],
                    ev.get("judge_model", model_name),
                    ev.get("timestamp", "")
                ])

    # Summary Statistics Calculation
    c_stat = compute_statistics(c_scores)
    f_stat = compute_statistics(f_scores)
    h_stat = compute_statistics(h_scores)
    a_stat = compute_statistics(a_scores)
    ov_stat = compute_statistics(overall_scores)

    print(f"\n{'='*75}")
    print(f"G-EVAL EVALUATION EXPERIMENT SUMMARY ({len(results)} recipes evaluated)")
    print(f"{'='*75}")
    print(f"Correctness Score (C)         : {c_stat['mean']:.4f} ± {c_stat['std']:.4f}")
    print(f"Faithfulness Score (F)        : {f_stat['mean']:.4f} ± {f_stat['std']:.4f}")
    print(f"Hallucination-Free Score (H)  : {h_stat['mean']:.4f} ± {h_stat['std']:.4f}")
    print(f"Constraint Adherence Score (A): {a_stat['mean']:.4f} ± {a_stat['std']:.4f}")
    print(f"{'-'*75}")
    print(f"OVERALL EVALUATION SCORE (AVG): {ov_stat['mean']:.4f} ± {ov_stat['std']:.4f}")
    print(f"{'='*75}")
    print(f"Results saved to JSONL: {output_jsonl}")
    print(f"Results saved to CSV  : {output_csv}")
    print(f"{'='*75}\n")

    # Generate LaTeX Table snippet for Research Paper
    latex_table = f"""
% LaTeX Table for RecipeFusion Academic Paper
\\begin{{table}}[ht]
\\centering
\\small
\\begin{{tabular}}{{lccccc}}
\\toprule
\\textbf{{Judge Model}} & \\textbf{{Correctness}} & \\textbf{{Faithfulness}} & \\textbf{{Hallucination-free}} & \\textbf{{Constraint Adh.}} & \\textbf{{Overall}} \\\\
\\midrule
{model_name.split('/')[-1]} & {c_stat['mean']:.3f} $\\pm$ {c_stat['std']:.3f} & {f_stat['mean']:.3f} $\\pm$ {f_stat['std']:.3f} & {h_stat['mean']:.3f} $\\pm$ {h_stat['std']:.3f} & {a_stat['mean']:.3f} $\\pm$ {a_stat['std']:.3f} & \\textbf{{{ov_stat['mean']:.3f} $\\pm$ {ov_stat['std']:.3f}}} \\\\
\\bottomrule
\\end{{tabular}}
\\caption{{G-Eval LLM-as-a-Judge evaluation results across four finalized dimensions ($N={len(results)}$).}}
\\label{{tab:geval_results}}
\\end{{table}}
"""
    latex_path = os.path.join(output_dir, f"table_geval_{clean_model_tag}.tex")
    with open(latex_path, "w", encoding="utf-8") as f:
        f.write(latex_table.strip())
    print(f"LaTeX Table snippet generated: {latex_path}\n")

    return {
        "correctness": c_stat,
        "faithfulness": f_stat,
        "hallucination": h_stat,
        "constraint_adherence": a_stat,
        "overall": ov_stat,
        "jsonl_path": output_jsonl,
        "csv_path": output_csv
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run G-Eval batch evaluation on novel recipes.")
    parser.add_argument("--input", default=os.path.join(PROJECT_ROOT, "memory", "eval_novel_recipes.json"),
                        help="Path to novel recipes JSON or JSONL file.")
    parser.add_argument("--output", default=os.path.join(PROJECT_ROOT, "evaluation", "results"),
                        help="Directory to save evaluation results.")
    parser.add_argument("--model", default=DEFAULT_JUDGE_MODEL,
                        help="LLM Judge model identifier (e.g. meta-llama/Meta-Llama-3-70B-Instruct).")
    parser.add_argument("--api-base", default=DEFAULT_VLLM_API_BASE,
                        help="OpenAI-compatible API base URL (e.g. http://localhost:8000/v1).")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit number of recipes to evaluate.")
    parser.add_argument("--fast", action="store_true",
                        help="Use single-pass unified JSON evaluation instead of sequential G-Eval.")

    args = parser.parse_args()
    run_batch_evaluation(
        input_file=args.input,
        output_dir=args.output,
        model_name=args.model,
        api_base=args.api_base,
        limit=args.limit,
        fast_mode=args.fast
    )
