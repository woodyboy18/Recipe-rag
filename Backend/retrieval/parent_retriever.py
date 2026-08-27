import pandas as pd
from typing import List, Dict, Set, Any
from core.schemas import QuerySpec
from ingredients.normalizer import normalize_ingredient_list

def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0

def retrieve_diverse_parents(
    query_spec: QuerySpec,
    df: pd.DataFrame,
    embed_model,
    faiss_index,
    bm25_model,
    ingredient_index=None,
    num_parents: int = 4
) -> List[Dict[str, Any]]:
    """
    Retrieves 3-5 diverse parent recipes covering required ingredients, dish technique, and supporting items.
    Uses Maximal Marginal Relevance (MMR) & Jaccard ingredient diversification to prevent duplicate parents.
    """
    req_ings = set(normalize_ingredient_list(query_spec.ingredients_to_include))
    avoid_ings = set(normalize_ingredient_list(query_spec.ingredients_to_avoid))

    # Candidate pool generation
    candidates = []

    # 1. Retrieve candidates for each required ingredient individually
    if req_ings:
        for ing in req_ings:
            spec_ing = QuerySpec(
                original_query=f"{query_spec.meal or ''} {ing}",
                ingredients_to_include=[ing],
                ingredients_to_avoid=list(avoid_ings)
            )
            from retrieval.hybrid_retriever import retrieve_hybrid_rrf
            docs, _ = retrieve_hybrid_rrf(spec_ing, df, embed_model, faiss_index, bm25_model, ingredient_index, top_k=5)
            candidates.extend(docs)

    # 2. Retrieve candidates for meal type / technique / general query
    gen_query = f"{query_spec.meal or ''} {' '.join(req_ings)}"
    spec_gen = QuerySpec(
        original_query=gen_query.strip(),
        ingredients_to_avoid=list(avoid_ings)
    )
    from retrieval.hybrid_retriever import retrieve_hybrid_rrf
    gen_docs, _ = retrieve_hybrid_rrf(spec_gen, df, embed_model, faiss_index, bm25_model, ingredient_index, top_k=10)
    candidates.extend(gen_docs)

    # Deduplicate candidates by recipe_id
    unique_candidates = []
    seen_ids = set()
    for doc in candidates:
        r_id = doc["recipe_id"]
        if r_id not in seen_ids:
            seen_ids.add(r_id)
            unique_candidates.append(doc)

    if not unique_candidates:
        return []

    # Diversify selection using Greedy Jaccard MMR
    selected_parents: List[Dict[str, Any]] = []
    
    # Always pick highest scored candidate as first parent
    selected_parents.append(unique_candidates[0])

    for _ in range(1, min(num_parents, len(unique_candidates))):
        best_cand = None
        best_diversity_score = -1.0

        for cand in unique_candidates:
            if cand in selected_parents:
                continue

            cand_ings = set(cand.get("normalized_ingredients", []))
            
            # Compute max similarity against already selected parents
            max_sim = max([jaccard_similarity(cand_ings, set(p.get("normalized_ingredients", []))) for p in selected_parents])

            # Coverage bonus for covering an un-covered required ingredient
            covered = set()
            for p in selected_parents:
                covered.update(p.get("normalized_ingredients", []))
            
            uncovered_req = req_ings - covered
            coverage_bonus = 0.5 if cand_ings.intersection(uncovered_req) else 0.0

            # Score = low similarity to existing + coverage bonus
            score = (1.0 - max_sim) + coverage_bonus
            if score > best_diversity_score:
                best_diversity_score = score
                best_cand = cand

        if best_cand and best_cand not in selected_parents:
            selected_parents.append(best_cand)

    return selected_parents
