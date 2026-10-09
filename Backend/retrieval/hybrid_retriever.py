import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Set, Any, Optional
from core.schemas import QuerySpec
from ingredients.ingredient_index import IngredientIndex

def retrieve_hybrid_rrf(
    query_spec: QuerySpec,
    df: pd.DataFrame,
    embed_model,
    faiss_index,
    bm25_model,
    ingredient_index: Optional[IngredientIndex] = None,
    top_k: int = 10,
    rrf_k: int = 60
) -> Tuple[List[Dict[str, Any]], List[Any]]:
    """
    Candidate-filtered hybrid retrieval using Reciprocal Rank Fusion (RRF) over FAISS + BM25 scores.
    Strictly enforces mandatory ingredient inclusion and avoided ingredient exclusion.
    """
    total_docs = len(df)
    if total_docs == 0:
        return [], []

    req_ings = query_spec.ingredients_to_include
    avoid_ings = query_spec.ingredients_to_avoid

    # 1. Determine Candidate Recipe IDs
    if ingredient_index:
        candidate_ids = ingredient_index.find_candidate_recipe_ids(
            required_ingredients=req_ings,
            avoided_ingredients=avoid_ings
        )
    else:
        # Fallback inline dataframe filtering if ingredient_index not provided
        candidate_ids = set()
        for idx, row in df.iterrows():
            rec_id = row.get("recipe_id", idx)
            doc_text = str(row.get("document", "")).lower()

            # Check avoidance
            has_avoid = False
            for a in avoid_ings:
                if a in doc_text:
                    has_avoid = True
                    break
            if has_avoid:
                continue

            # Check required
            has_all_req = True
            for r in req_ings:
                if r not in doc_text:
                    has_all_req = False
                    break
            if has_all_req:
                candidate_ids.add(rec_id)

    # If required ingredients were specified and no candidates match exact intersection
    if req_ings and not candidate_ids:
        return [], []

    # Map candidate_ids to dataframe integer positional indices
    id_to_pos = {}
    for pos, row in df.iterrows():
        r_id = row.get("recipe_id", pos)
        if not candidate_ids or r_id in candidate_ids:
            id_to_pos[r_id] = pos

    if not id_to_pos:
        return [], []

    candidate_positions = set(id_to_pos.values())

    # 2. FAISS Top 30 Search
    pos_query = query_spec.original_query
    emb = embed_model.encode([pos_query])
    faiss_k = min(50, total_docs)
    distances, raw_faiss_indices = faiss_index.search(np.array(emb), faiss_k)

    faiss_ranks = {}
    rank_count = 1
    for f_pos in raw_faiss_indices[0]:
        if f_pos != -1 and f_pos < total_docs:
            if f_pos in candidate_positions:
                faiss_ranks[f_pos] = rank_count
                rank_count += 1

    # 3. BM25 Top Search with Stop Words Filtered
    STOP_WORDS = {
        "give", "me", "recipe", "recipes", "using", "for", "with", "show", "find", 
        "item", "items", "made", "including", "having", "containing", "a", "an", 
        "the", "in", "of", "and", "or", "to", "create", "invent", "make", "cook", "new"
    }
    raw_tokens = pos_query.lower().split()
    query_tokens = [tok for tok in raw_tokens if tok not in STOP_WORDS]
    if not query_tokens:
        query_tokens = raw_tokens

    bm25_scores = bm25_model.get_scores(query_tokens)
    top_bm25_positions = np.argsort(bm25_scores)[::-1]

    bm25_ranks = {}
    rank_count = 1
    for b_pos in top_bm25_positions:
        if b_pos < total_docs and b_pos in candidate_positions:
            bm25_ranks[b_pos] = rank_count
            rank_count += 1
            if rank_count > 100:
                break

    # 4. Compute RRF Scores
    rrf_scores = {}
    for pos in candidate_positions:
        faiss_r = faiss_ranks.get(pos, 1000)
        bm25_r = bm25_ranks.get(pos, 1000)

        score = (1.0 / (rrf_k + faiss_r)) + (1.0 / (rrf_k + bm25_r))
        rrf_scores[pos] = score

    # Sort positions by RRF score descending
    sorted_positions = sorted(rrf_scores.keys(), key=lambda p: rrf_scores[p], reverse=True)

    retrieved_docs = []
    retrieved_indices = []

    for pos in sorted_positions[:top_k]:
        row = df.iloc[pos]
        rec_id = row.get("recipe_id", pos)
        doc_dict = {
            "recipe_id": rec_id,
            "title": row.get("title", f"Recipe {rec_id}"),
            "ingredients": row.get("ingredients", ""),
            "normalized_ingredients": row.get("normalized_ingredients", []),
            "instructions": row.get("instructions", ""),
            "document": row.get("document", ""),
            "rrf_score": round(rrf_scores[pos], 4)
        }
        retrieved_docs.append(doc_dict)
        retrieved_indices.append(pos)

    return retrieved_docs, retrieved_indices
