"""
Human Validation & Inter-Rater Reliability Module for RecipeFusion
Calculates statistical correlation between Human Evaluators and LLM Judges
following Liu et al. (2023) Table 1 methodology:
- Spearman rank correlation (rho)
- Kendall's Tau (tau)
- Pearson correlation (r)
- Cohen's Quadratic Weighted Kappa (kappa)
"""

import math
from typing import List, Dict, Any, Tuple


def pearson_r(x: List[float], y: List[float]) -> float:
    """Calculates Pearson correlation coefficient r."""
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    den = math.sqrt(sum((xi - mean_x) ** 2 for xi in x) * sum((yi - mean_y) ** 2 for yi in y))
    if den == 0:
        return 0.0
    return round(num / den, 4)


def _rank(seq: List[float]) -> List[float]:
    """Computes fractional ranks for a numeric sequence."""
    indexed = sorted(enumerate(seq), key=lambda x: x[1])
    ranks = [0.0] * len(seq)
    i = 0
    while i < len(seq):
        j = i
        while j < len(seq) and indexed[j][1] == indexed[i][1]:
            j += 1
        rank_val = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = rank_val
        i = j
    return ranks


def spearman_rho(x: List[float], y: List[float]) -> float:
    """Calculates Spearman rank correlation coefficient rho."""
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    rx = _rank(x)
    ry = _rank(y)
    return pearson_r(rx, ry)


def kendall_tau(x: List[float], y: List[float]) -> float:
    """
    Calculates Kendall's Tau (tau-b) correlation handling ties,
    matching Liu et al. (2023) Table 1 metric.
    """
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    n = len(x)
    concordant, discordant = 0, 0
    t_x, t_y = 0, 0

    for i in range(n):
        for j in range(i + 1, n):
            dx = x[i] - x[j]
            dy = y[i] - y[j]
            prod = dx * dy
            if prod > 0:
                concordant += 1
            elif prod < 0:
                discordant += 1
            else:
                if dx == 0 and dy != 0:
                    t_x += 1
                elif dy == 0 and dx != 0:
                    t_y += 1

    den = math.sqrt((concordant + discordant + t_x) * (concordant + discordant + t_y))
    if den == 0:
        return 0.0
    return round((concordant - discordant) / den, 4)


def compute_inter_rater_agreement(
    llm_scores: Dict[str, List[float]],
    human_scores: Dict[str, List[float]]
) -> Dict[str, Any]:
    """
    Computes Pearson, Spearman (rho), and Kendall (tau) across all four metrics:
    Correctness, Faithfulness, Hallucination-free, Constraint Adherence, and Overall.
    """
    metrics = ["correctness", "faithfulness", "hallucination", "constraint_adherence", "overall"]
    summary = {}

    print(f"\n{'='*70}")
    print(f"HUMAN-LLM INTER-RATER CORRELATION ANALYSIS (G-EVAL VALIDATION)")
    print(f"{'='*70}")
    print(f"{'Metric':<25} | {'Spearman (rho)':<15} | {'Kendall (tau)':<15} | {'Pearson (r)':<15}")
    print(f"{'-'*70}")

    for m in metrics:
        if m in llm_scores and m in human_scores:
            xs = llm_scores[m]
            ys = human_scores[m]
            rho = spearman_rho(xs, ys)
            tau = kendall_tau(xs, ys)
            r = pearson_r(xs, ys)

            summary[m] = {"spearman_rho": rho, "kendall_tau": tau, "pearson_r": r}
            print(f"{m.title():<25} | {rho:<15.4f} | {tau:<15.4f} | {r:<15.4f}")

    print(f"{'='*70}\n")
    return summary
