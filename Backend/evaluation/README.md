# RecipeFusion G-Eval LLM-as-a-Judge Evaluation Framework

This module implements an independent, academically rigorous evaluation framework for **RecipeFusion**, strictly adhering to the methodology established in:
> **Liu et al. (2023)**, *"G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment"*.

---

## 1. The Four Final Evaluation Metrics (0.0 – 1.0)

| Metric | Target | Scoring Method |
| :--- | :--- | :--- |
| **1. Correctness** | Feasibility, chronological/thermodynamic soundness, accurate ingredient ratios, absence of contradictory cooking steps. | G-Eval CoT + Token Logprob Expectation $\in [0.0, 1.0]$ |
| **2. Faithfulness** | Grounded in retrieved RecipeDB parent evidence without copying. Creative transformations are welcomed; only distortions/contradictions are penalized. | G-Eval CoT + Token Logprob Expectation $\in [0.0, 1.0]$ |
| **3. Hallucination-Free** | Absence of fabricated ingredients, impossible physical transformations, or false nutritional assertions. (1.0 = flawless, 0.0 = severe hallucinations). | G-Eval CoT + Token Logprob Expectation $\in [0.0, 1.0]$ |
| **4. Constraint Adherence** | Absolute compliance with user's explicit inclusions, exclusions (allergens/diets), time limits, and meal types. Hard exclusions receive 0.0 if breached. | G-Eval CoT + Token Logprob Expectation $\in [0.0, 1.0]$ |

$$\text{Overall Score} = \frac{\text{Correctness} + \text{Faithfulness} + \text{Hallucination} + \text{Constraint Adherence}}{4} \in [0.0, 1.0]$$

---

## 2. File Overview

- `evaluation_prompts.py`: Formal task definitions, explicit Chain-of-Thought (CoT) evaluation steps, and 1-to-5 calibrated rubrics.
- `llm_judge.py`: Model-agnostic evaluator supporting vLLM OpenAI-compatible endpoints with token probability expectation calculation:
  $$\mathbb{E}[s] = \sum_{i=1}^5 i \cdot p(i) \implies \text{Score} = \frac{\mathbb{E}[s] - 1}{4} \in [0.0, 1.0]$$
- `eval_dataset_generator.py`: Generates the 10–15 novel recipes using 15 diverse benchmark queries, saving complete triplets into `eval_novel_recipes.json` and `user_memory.json`.
- `batch_evaluator.py`: CLI batch orchestrator that evaluates recipes, computes means and standard deviations, and produces JSONL, CSV, and LaTeX tables.
- `human_validation.py`: Statistical correlation module (Spearman's $\rho$, Kendall's $\tau$, Pearson's $r$).
- `serve_vllm.sh`: Production bash script to deploy Llama 3 70B across 2× A100 (80GB) GPUs using Tensor Parallelism.

---

## 3. Workflow Instructions

### Step 1: Generate 10–15 Novel Recipes on Your Local PC
In your Python environment, run:
```bash
python Backend/evaluation/eval_dataset_generator.py 15
```
*(Or use your existing Streamlit / API frontend — full recipe triplets and parent recipes will automatically be saved into `Backend/memory/eval_novel_recipes.json` and `Backend/memory/user_memory.json`)*.

### Step 2: Push to College Server (2 × A100 80GB)
Once your 10–15 recipes are saved, push your repository to your college server:
```bash
git add Backend/evaluation Backend/memory/eval_novel_recipes.json Backend/memory/user_memory.json
git commit -m "Add G-Eval evaluation framework and 15 test novel recipes"
git push origin main
```

### Step 3: On the College Server — Serve Llama 3 70B via vLLM
SSH into your server and run:
```bash
bash Backend/evaluation/serve_vllm.sh llama3
```
vLLM will serve `meta-llama/Meta-Llama-3-70B-Instruct` on `http://localhost:8000/v1` with Tensor Parallelism (`tp=2`) in native BF16 across both A100 GPUs.

### Step 4: Run the G-Eval Batch Evaluator
In a separate terminal on the server:
```bash
python Backend/evaluation/batch_evaluator.py \
    --input Backend/memory/eval_novel_recipes.json \
    --model meta-llama/Meta-Llama-3-70B-Instruct \
    --api-base http://localhost:8000/v1
```

The script will evaluate all recipes and output:
1. `eval_results_Meta_Llama_3_70B_Instruct_<timestamp>.jsonl`
2. `eval_results_Meta_Llama_3_70B_Instruct_<timestamp>.csv`
3. `table_geval_Meta_Llama_3_70B_Instruct.tex` (ready for your paper)
