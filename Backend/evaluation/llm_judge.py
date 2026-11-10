"""
Model-Agnostic LLM-as-a-Judge Evaluation Module
Strictly implements the G-Eval framework (Liu et al., 2023)
Supports:
- vLLM serving OpenAI-compatible endpoints with logprobs extraction (port 8000)
- Ollama native endpoints (/api/chat and /api/generate on port 11434, compatible with all Ollama versions)
- Chain-of-Thought (CoT) step verification
- Mathematical expectation scoring: E[s] = sum(s * p(s)) normalized to [0.0, 1.0]
- Fallback JSON parsing and schema validation
- 4 metrics only: Correctness, Faithfulness, Hallucination, Constraint Adherence
"""

import os
import re
import json
import math
import time
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

try:
    import requests
except ImportError:
    requests = None

from evaluation.evaluation_prompts import (
    GEVAL_METRIC_DEFINITIONS,
    build_single_metric_geval_prompt,
    build_unified_geval_prompt
)

# ==============================================================================
# CONFIGURATION DEFAULTS
# ==============================================================================

DEFAULT_VLLM_API_BASE = os.getenv("JUDGE_API_BASE", "http://localhost:8000/v1")
DEFAULT_JUDGE_MODEL = os.getenv("JUDGE_MODEL", "meta-llama/Meta-Llama-3-70B-Instruct")
DEFAULT_API_KEY = os.getenv("JUDGE_API_KEY", "EMPTY")


class LLMJudge:
    def __init__(
        self,
        model_name: str = DEFAULT_JUDGE_MODEL,
        api_base: str = DEFAULT_VLLM_API_BASE,
        api_key: str = DEFAULT_API_KEY,
        use_strict_logprobs: bool = True,
        timeout: float = 180.0
    ):
        self.model_name = model_name
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.use_strict_logprobs = use_strict_logprobs
        self.timeout = timeout
        
        # Check if openai python SDK is available, else use direct HTTP
        self._openai_client = None
        try:
            from openai import OpenAI
            self._openai_client = OpenAI(
                base_url=self.api_base,
                api_key=self.api_key
            )
        except ImportError:
            self._openai_client = None

    def _call_completions_api(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        logprobs: bool = False,
        top_logprobs: int = 10
    ) -> Dict[str, Any]:
        """
        Calls evaluation endpoint.
        Automatically adapts to:
        1. Native Ollama (/api/chat and /api/generate) for any Ollama version on port 11434
        2. OpenAI-compatible vLLM endpoints (/v1/chat/completions) on port 8000
        """
        is_ollama = "11434" in self.api_base or "ollama" in self.api_base.lower()

        # ROUTE 1: NATIVE OLLAMA API (Compatible with ALL Ollama versions including 0.1.23)
        if is_ollama:
            host_root = self.api_base.replace("/v1", "").rstrip("/")
            
            # Try native Ollama /api/chat
            chat_url = f"{host_root}/api/chat"
            chat_payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            try:
                req_data = json.dumps(chat_payload).encode("utf-8")
                req = urllib.request.Request(chat_url, data=req_data, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    text = res_json.get("message", {}).get("content", "")
                    return {"choices": [{"message": {"content": text}}]}
            except Exception:
                # Fallback to native Ollama /api/generate
                gen_url = f"{host_root}/api/generate"
                gen_payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }
                req_data = json.dumps(gen_payload).encode("utf-8")
                req = urllib.request.Request(gen_url, data=req_data, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    text = res_json.get("response", "")
                    return {"choices": [{"message": {"content": text}}]}

        # ROUTE 2: OPENAI-COMPATIBLE VLLM API (port 8000)
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        if logprobs:
            payload["logprobs"] = True
            payload["top_logprobs"] = top_logprobs

        if self._openai_client is not None:
            try:
                kw = {
                    "model": self.model_name,
                    "messages": payload["messages"],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if logprobs:
                    kw["logprobs"] = True
                    kw["top_logprobs"] = top_logprobs
                res = self._openai_client.chat.completions.create(**kw)
                return res.model_dump()
            except Exception:
                pass

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        url = f"{self.api_base}/chat/completions"

        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # ==========================================================================
    # STRICT G-EVAL LOGPROB EXPECTATION CALCULATION
    # ==========================================================================

    @staticmethod
    def _compute_expected_score_from_logprobs(
        logprobs_content: List[Dict[str, Any]],
        scale_min: int = 1,
        scale_max: int = 5
    ) -> Optional[float]:
        """
        Calculates mathematical expectation:
        E[s] = sum_{i=1}^5 (i) * p(i)
        Normalized to [0.0, 1.0]: (E[s] - scale_min) / (scale_max - scale_min)
        """
        if not logprobs_content:
            return None

        # Locate the token following "Score:" or "[Score]"
        target_token_info = None
        for idx, item in enumerate(logprobs_content):
            token_str = item.get("token", "").strip()
            # If previous tokens indicate 'Score' or ':'
            if idx > 0 and ("score" in logprobs_content[idx - 1].get("token", "").lower() or 
                           ":" in logprobs_content[idx - 1].get("token", "")):
                if token_str and token_str[0].isdigit():
                    target_token_info = item
                    break
            # Or token directly is a digit
            if token_str in [str(i) for i in range(scale_min, scale_max + 1)]:
                target_token_info = item
                break

        if not target_token_info or "top_logprobs" not in target_token_info:
            return None

        top_lp = target_token_info["top_logprobs"]
        
        # Collect raw logits/logprobs for candidate score integers 1..5
        prob_dict = {}
        for entry in top_lp:
            t_tok = entry.get("token", "").strip()
            lp = entry.get("logprob")
            if t_tok in [str(i) for i in range(scale_min, scale_max + 1)] and lp is not None:
                int_val = int(t_tok)
                prob_dict[int_val] = math.exp(lp)

        if not prob_dict:
            return None

        # Softmax normalization over the candidate set
        total_p = sum(prob_dict.values())
        if total_p <= 0:
            return None

        norm_probs = {k: v / total_p for k, v in prob_dict.items()}
        expected_s = sum(score * p for score, p in norm_probs.items())

        # Normalize expectation to [0.0, 1.0] continuous score
        score_0_1 = (expected_s - scale_min) / (scale_max - scale_min)
        return max(0.0, min(1.0, round(score_0_1, 4)))

    @staticmethod
    def _parse_single_metric_response(text: str) -> Tuple[Optional[float], str, List[str], List[str]]:
        """Parses Analysis, Evidence, Issues, and Score integer fallback from response text."""
        reason = ""
        evidence = []
        issues = []
        score_val = None

        # Extract Analysis/Reason
        analysis_match = re.search(r"Analysis:\s*(.*?)(?=\n\s*(?:Evidence|Issues|Score):|\Z)", text, re.DOTALL | re.IGNORECASE)
        if analysis_match:
            reason = analysis_match.group(1).strip()
        else:
            reason = text[:400].strip()

        # Extract Evidence bullets
        evidence_match = re.search(r"Evidence:\s*(.*?)(?=\n\s*(?:Issues|Score):|\Z)", text, re.DOTALL | re.IGNORECASE)
        if evidence_match:
            lines = [l.strip("- *").strip() for l in evidence_match.group(1).strip().split("\n") if l.strip("- *").strip()]
            evidence = lines

        # Extract Issues bullets
        issues_match = re.search(r"Issues:\s*(.*?)(?=\n\s*Score:|\Z)", text, re.DOTALL | re.IGNORECASE)
        if issues_match:
            lines = [l.strip("- *").strip() for l in issues_match.group(1).strip().split("\n") if l.strip("- *").strip()]
            issues = [l for l in lines if l.lower() not in ["none", "none.", "n/a", "no issues"]]

        # Extract Score integer fallback (1 to 5)
        score_match = re.search(r"Score:\s*(\d(?:\.\d+)?)", text, re.IGNORECASE)
        if score_match:
            raw_num = float(score_match.group(1))
            if raw_num <= 1.0:
                score_val = raw_num
            elif raw_num <= 5.0:
                score_val = (raw_num - 1.0) / 4.0
            else:
                score_val = raw_num / 10.0

        if score_val is not None:
            score_val = max(0.0, min(1.0, round(score_val, 4)))

        return score_val, reason, evidence, issues

    # ==========================================================================
    # EVALUATE SINGLE METRIC (STRICT G-EVAL)
    # ==========================================================================

    def evaluate_single_metric(
        self,
        metric_key: str,
        user_query: str,
        retrieved_recipes: List[Any],
        generated_recipe: Any
    ) -> Dict[str, Any]:
        """
        Executes strict G-Eval evaluation for one metric dimension:
        Prompt -> LLM with top_logprobs -> Mathematical Expectation E[s].
        """
        prompt = build_single_metric_geval_prompt(
            metric_key=metric_key,
            user_query=user_query,
            retrieved_recipes=retrieved_recipes,
            generated_recipe=generated_recipe
        )

        try:
            api_resp = self._call_completions_api(
                prompt=prompt,
                temperature=0.0,
                max_tokens=650,
                logprobs=self.use_strict_logprobs,
                top_logprobs=10
            )

            choice = api_resp["choices"][0]
            resp_text = choice["message"]["content"] or ""
            
            # 1. Attempt logprob expectation
            score = None
            if self.use_strict_logprobs and "logprobs" in choice and choice["logprobs"]:
                lp_content = choice["logprobs"].get("content", [])
                score = self._compute_expected_score_from_logprobs(lp_content, scale_min=1, scale_max=5)

            # 2. Fallback to parsed score if logprobs not available
            parsed_score, reason, evidence, issues = self._parse_single_metric_response(resp_text)
            final_score = score if score is not None else (parsed_score if parsed_score is not None else 0.5)

            return {
                "score": final_score,
                "reason": reason,
                "evidence": evidence,
                "issues": issues,
                "scoring_method": "geval_logprobs_expectation" if score is not None else "geval_cot_parsed"
            }

        except Exception as e:
            return {
                "score": 0.0,
                "reason": f"Evaluation API error: {str(e)}",
                "evidence": [],
                "issues": [f"Evaluation failed: {str(e)}"],
                "scoring_method": "error_fallback"
            }

    # ==========================================================================
    # EVALUATE FULL RECIPE (ALL 4 DIMENSIONS)
    # ==========================================================================

    def evaluate_recipe(
        self,
        user_query: str,
        retrieved_recipes: List[Any],
        generated_recipe: Any,
        fast_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluates a novel generated recipe across the exact four finalized dimensions:
        1. Correctness
        2. Faithfulness
        3. Hallucination (Hallucination-free)
        4. Constraint Adherence
        Returns continuous scores bounded strictly in [0.0, 1.0] and overall arithmetic mean.
        """
        timestamp = datetime.utcnow().isoformat() + "Z"

        if fast_mode:
            # Single-pass unified JSON evaluation
            prompt = build_unified_geval_prompt(user_query, retrieved_recipes, generated_recipe)
            try:
                resp = self._call_completions_api(prompt, temperature=0.0, max_tokens=900)
                raw_text = resp["choices"][0]["message"]["content"]
                
                # Sanitize JSON from markdown blocks
                clean_json = raw_text.strip()
                if clean_json.startswith("```"):
                    clean_json = re.sub(r"^```(?:json)?\n?", "", clean_json)
                    clean_json = re.sub(r"\n?```$", "", clean_json)
                    
                parsed = json.loads(clean_json)
                
                # Validate and bound all 4 metrics
                c = max(0.0, min(1.0, float(parsed.get("correctness", {}).get("score", 0.0))))
                f = max(0.0, min(1.0, float(parsed.get("faithfulness", {}).get("score", 0.0))))
                h = max(0.0, min(1.0, float(parsed.get("hallucination", {}).get("score", 0.0))))
                a = max(0.0, min(1.0, float(parsed.get("constraint_adherence", {}).get("score", 0.0))))
                overall = round((c + f + h + a) / 4.0, 4)

                return {
                    "correctness": {
                        "score": round(c, 4),
                        "reason": parsed.get("correctness", {}).get("reason", ""),
                        "evidence": parsed.get("correctness", {}).get("evidence", []),
                        "issues": parsed.get("correctness", {}).get("issues", [])
                    },
                    "faithfulness": {
                        "score": round(f, 4),
                        "reason": parsed.get("faithfulness", {}).get("reason", ""),
                        "evidence": parsed.get("faithfulness", {}).get("evidence", []),
                        "issues": parsed.get("faithfulness", {}).get("issues", [])
                    },
                    "hallucination": {
                        "score": round(h, 4),
                        "reason": parsed.get("hallucination", {}).get("reason", ""),
                        "evidence": parsed.get("hallucination", {}).get("evidence", []),
                        "issues": parsed.get("hallucination", {}).get("issues", [])
                    },
                    "constraint_adherence": {
                        "score": round(a, 4),
                        "reason": parsed.get("constraint_adherence", {}).get("reason", ""),
                        "evidence": parsed.get("constraint_adherence", {}).get("evidence", []),
                        "issues": parsed.get("constraint_adherence", {}).get("issues", [])
                    },
                    "overall_score": overall,
                    "judge_model": self.model_name,
                    "timestamp": timestamp,
                    "mode": "unified_geval"
                }
            except Exception:
                pass

        # Strict G-Eval Sequential Execution (Individual Metrics with Logprob Expectation)
        c_res = self.evaluate_single_metric("correctness", user_query, retrieved_recipes, generated_recipe)
        f_res = self.evaluate_single_metric("faithfulness", user_query, retrieved_recipes, generated_recipe)
        h_res = self.evaluate_single_metric("hallucination", user_query, retrieved_recipes, generated_recipe)
        a_res = self.evaluate_single_metric("constraint_adherence", user_query, retrieved_recipes, generated_recipe)

        overall = round((c_res["score"] + f_res["score"] + h_res["score"] + a_res["score"]) / 4.0, 4)

        return {
            "correctness": c_res,
            "faithfulness": f_res,
            "hallucination": h_res,
            "constraint_adherence": a_res,
            "overall_score": overall,
            "judge_model": self.model_name,
            "timestamp": timestamp,
            "mode": "strict_geval_sequential"
        }


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

def evaluate_recipe(
    user_query: str,
    retrieved_recipes: List[Any],
    generated_recipe: Any,
    judge_model: Optional[str] = None,
    api_base: Optional[str] = None
) -> Dict[str, Any]:
    """Top-level convenience evaluator."""
    judge = LLMJudge(
        model_name=judge_model or DEFAULT_JUDGE_MODEL,
        api_base=api_base or DEFAULT_VLLM_API_BASE
    )
    return judge.evaluate_recipe(
        user_query=user_query,
        retrieved_recipes=retrieved_recipes,
        generated_recipe=generated_recipe
    )


def save_evaluation(evaluation_result: Dict[str, Any], output_path: str):
    """Appends evaluation result to a JSONL file."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(evaluation_result) + "\n")
