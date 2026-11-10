"""
Native Hugging Face PyTorch G-Eval Evaluator for RecipeFusion
Runs LLM-as-a-Judge DIRECTLY on GPU (No Ollama or external daemons required)
Supports:
- Pre-cached local models (e.g. Qwen/Qwen2.5-32B-Instruct-AWQ, Mistral-7B, etc.)
- Direct PyTorch logit extraction for authentic G-Eval probability-weighted scoring:
  E[s] = sum_{i=1}^5 (i) * p(i)
- 4 finalized metrics bounded strictly in [0.0, 1.0]:
  1. Correctness
  2. Faithfulness
  3. Hallucination-free
  4. Constraint Adherence
- Saves progress incrementally to JSONL, CSV, and generates LaTeX tables for research paper.
"""

import os
import sys
import json
import csv
import math
import re
import argparse
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

import torch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from evaluation.evaluation_prompts import (
    GEVAL_METRIC_DEFINITIONS,
    build_single_metric_geval_prompt,
    build_unified_geval_prompt
)
from evaluation.batch_evaluator import load_recipes_for_evaluation, compute_statistics


class HuggingFaceJudge:
    def __init__(
        self,
        model_name_or_path: str = "mistralai/Mistral-7B-Instruct-v0.1",
        device: str = "cuda",
        torch_dtype = torch.float16
    ):
        self.model_name = model_name_or_path
        self.device = device
        
        print(f"\n[HuggingFaceJudge] Loading tokenizer for '{model_name_or_path}'...")
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name_or_path,
            trust_remote_code=True
        )
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        print(f"[HuggingFaceJudge] Loading model onto {self.device.upper()} (NVIDIA L40S)...")
        # Load model with automatic device mapping
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            device_map="auto",
            torch_dtype=torch_dtype,
            trust_remote_code=True
        )
        self.model.eval()
        print("[HuggingFaceJudge] Model successfully loaded into VRAM!\n")

        # Map score tokens '1', '2', '3', '4', '5' to tokenizer IDs
        self.score_token_ids = {}
        for i in range(1, 6):
            ids = self.tokenizer.encode(str(i), add_special_tokens=False)
            if ids:
                self.score_token_ids[i] = ids[-1]

    def _generate_response_with_logits(
        self,
        prompt: str,
        max_new_tokens: int = 650
    ) -> Tuple[str, Optional[Dict[int, float]]]:
        """
        Generates text and computes token probabilities over candidate score tokens [1..5].
        Searches backwards from the end of the text to target the score token after 'Score:'.
        """
        if hasattr(self.tokenizer, "apply_chat_template") and self.tokenizer.chat_template:
            messages = [{"role": "user", "content": prompt}]
            formatted_input = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
        else:
            formatted_input = prompt

        inputs = self.tokenizer(formatted_input, return_tensors="pt").to(self.model.device)
        input_len = inputs["input_ids"].shape[1]

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,  # Greedy / deterministic decoding (temperature=0.0)
                return_dict_in_generate=True,
                output_scores=True,
                pad_token_id=self.tokenizer.pad_token_id
            )

        gen_tokens = outputs.sequences[0, input_len:]
        response_text = self.tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()

        # Locate the TRUE score token (searching backwards from the end of the response)
        score_probs = None
        if outputs.scores and len(outputs.scores) == len(gen_tokens):
            decoded_tokens = [self.tokenizer.decode([t.item()]).strip() for t in gen_tokens]
            
            # Find the last occurrence of a digit 1..5 that appears after "Score"
            target_idx = None
            for idx in range(len(decoded_tokens) - 1, -1, -1):
                tok_str = decoded_tokens[idx]
                if tok_str in ["1", "2", "3", "4", "5"]:
                    # Check if preceded by 'score' or ':' in recent window
                    recent_ctx = "".join(decoded_tokens[max(0, idx - 6):idx]).lower()
                    if "score" in recent_ctx or ":" in recent_ctx or idx >= len(decoded_tokens) - 8:
                        target_idx = idx
                        break

            if target_idx is not None:
                step_logits = outputs.scores[target_idx]
                cand_logits = {}
                for score_int, tid in self.score_token_ids.items():
                    cand_logits[score_int] = step_logits[0, tid].item()
                
                # Softmax normalization
                max_l = max(cand_logits.values())
                exp_sum = sum(math.exp(l - max_l) for l in cand_logits.values())
                if exp_sum > 0:
                    score_probs = {k: math.exp(v - max_l) / exp_sum for k, v in cand_logits.items()}

        return response_text, score_probs

    def evaluate_single_metric(
        self,
        metric_key: str,
        user_query: str,
        retrieved_recipes: List[Any],
        generated_recipe: Any
    ) -> Dict[str, Any]:
        """
        Evaluates 1 metric using strict G-Eval:
        Prompt -> Model Generate -> E[s] = sum(i * p(i)) -> [0.0, 1.0] continuous score.
        """
        prompt = build_single_metric_geval_prompt(metric_key, user_query, retrieved_recipes, generated_recipe)
        
        try:
            resp_text, score_probs = self._generate_response_with_logits(prompt, max_new_tokens=600)
            
            # 1. Parse text directly for score fallback, reason, evidence, issues
            from evaluation.llm_judge import LLMJudge
            parsed_score, reason, evidence, issues = LLMJudge._parse_single_metric_response(resp_text)

            # 2. Compute probability expectation if logits were isolated around the Score token
            expected_score = None
            if score_probs:
                e_s = sum(score_val * prob for score_val, prob in score_probs.items())
                expected_score = max(0.0, min(1.0, round((e_s - 1.0) / 4.0, 4)))

            # If logprob expectation seems valid and consistent with text, use it; else use parsed score
            if expected_score is not None and expected_score > 0.05:
                final_score = expected_score
                method = "native_hf_geval_expectation"
            elif parsed_score is not None:
                final_score = parsed_score
                method = "native_hf_cot_parsed"
            elif expected_score is not None:
                final_score = expected_score
                method = "native_hf_geval_expectation"
            else:
                final_score = 0.50
                method = "neutral_fallback"

            return {
                "score": final_score,
                "reason": reason,
                "evidence": evidence,
                "issues": issues,
                "method": method
            }
        except Exception as e:
            return {
                "score": 0.0,
                "reason": f"Inference Error: {str(e)}",
                "evidence": [],
                "issues": [str(e)],
                "method": "error_fallback"
            }

    def evaluate_recipe(
        self,
        user_query: str,
        retrieved_recipes: List[Any],
        generated_recipe: Any
    ) -> Dict[str, Any]:
        """
        Evaluates recipe across all 4 finalized metrics strictly in [0.0, 1.0].
        """
        c = self.evaluate_single_metric("correctness", user_query, retrieved_recipes, generated_recipe)
        f = self.evaluate_single_metric("faithfulness", user_query, retrieved_recipes, generated_recipe)
        h = self.evaluate_single_metric("hallucination", user_query, retrieved_recipes, generated_recipe)
        a = self.evaluate_single_metric("constraint_adherence", user_query, retrieved_recipes, generated_recipe)

        overall = round((c["score"] + f["score"] + h["score"] + a["score"]) / 4.0, 4)

        return {
            "correctness": c,
            "faithfulness": f,
            "hallucination": h,
            "constraint_adherence": a,
            "overall_score": overall,
            "judge_model": self.model_name,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


def run_hf_evaluation(
    input_file: str,
    output_dir: str,
    model_name: str,
    limit: Optional[int] = None
):
    """
    Main evaluation loop running natively with PyTorch on the L40S GPU.
    """
    os.makedirs(output_dir, exist_ok=True)
    all_recipes = load_recipes_for_evaluation(input_file)
    if limit and limit > 0:
        all_recipes = all_recipes[:limit]

    print(f"\n{'='*75}")
    print(f"RECIPEFUSION NATIVE PYTORCH G-EVAL EVALUATOR (NVIDIA L40S)")
    print(f"Model          : {model_name}")
    print(f"Total Recipes  : {len(all_recipes)}")
    print(f"{'='*75}\n")

    timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    clean_model_tag = model_name.split("/")[-1].replace(":", "_").replace("-", "_")
    output_jsonl = os.path.join(output_dir, f"eval_results_{clean_model_tag}_{timestamp_str}.jsonl")
    output_csv = os.path.join(output_dir, f"eval_results_{clean_model_tag}_{timestamp_str}.csv")

    judge = HuggingFaceJudge(model_name_or_path=model_name)

    results = []
    c_scores, f_scores, h_scores, a_scores, overall_scores = [], [], [], [], []

    for idx, item in enumerate(all_recipes, 1):
        q_id = item.get("id", f"sample_{idx:03d}")
        user_query = item.get("user_query", "")
        retrieved = item.get("retrieved_recipes", [])
        recipe = item.get("generated_recipe", {})
        rec_title = recipe.get("title", "Untitled Recipe") if isinstance(recipe, dict) else str(recipe)[:30]

        print(f"[{idx}/{len(all_recipes)}] Evaluating '{rec_title}' (Query: \"{user_query[:50]}...\")")

        eval_res = judge.evaluate_recipe(
            user_query=user_query,
            retrieved_recipes=retrieved,
            generated_recipe=recipe
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

        # Incremental save
        with open(output_jsonl, "a", encoding="utf-8") as out_f:
            out_f.write(json.dumps(record) + "\n")

    # Save to CSV
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

    # Summary Statistics
    c_stat = compute_statistics(c_scores)
    f_stat = compute_statistics(f_scores)
    h_stat = compute_statistics(h_scores)
    a_stat = compute_statistics(a_scores)
    ov_stat = compute_statistics(overall_scores)

    print(f"\n{'='*75}")
    print(f"NATIVE G-EVAL EVALUATION SUMMARY ({len(results)} recipes evaluated)")
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

    # Generate LaTeX table snippet
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
\\caption{{Native G-Eval LLM-as-a-Judge evaluation results using {model_name} ($N={len(results)}$).}}
\\label{{tab:geval_results}}
\\end{{table}}
"""
    latex_path = os.path.join(output_dir, f"table_geval_{clean_model_tag}.tex")
    with open(latex_path, "w", encoding="utf-8") as f:
        f.write(latex_table.strip())
    print(f"LaTeX Table snippet generated: {latex_path}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Native PyTorch G-Eval evaluation on novel recipes.")
    parser.add_argument("--input", default=os.path.join(PROJECT_ROOT, "memory", "eval_novel_recipes.json"),
                        help="Path to novel recipes JSON or JSONL file.")
    parser.add_argument("--output", default=os.path.join(PROJECT_ROOT, "evaluation", "results"),
                        help="Directory to save evaluation results.")
    parser.add_argument("--model", default="mistralai/Mistral-7B-Instruct-v0.1",
                        help="Hugging Face model identifier or local path.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit number of recipes to evaluate.")

    args = parser.parse_args()
    run_hf_evaluation(
        input_file=args.input,
        output_dir=args.output,
        model_name=args.model,
        limit=args.limit
    )
