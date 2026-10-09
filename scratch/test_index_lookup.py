import sys
import os
import pandas as pd

sys.path.insert(0, 'Backend')
import core.recipe_engine as re_engine
from constraints.constraint_extractor import parse_query_to_spec
from retrieval.hybrid_retriever import retrieve_hybrid_rrf

re_engine.initialize_engine()

df = re_engine._df
ing_idx = re_engine._ingredient_index

print(f"Total df rows: {len(df)}")
print(f"Ingredient Index size: {len(ing_idx.index)}")
print(f"asafoetida in index: {'asafoetida' in ing_idx.index}")

if 'asafoetida' in ing_idx.index:
    cids = ing_idx.index['asafoetida']
    print(f"Found {len(cids)} candidate recipe IDs for asafoetida: {list(cids)[:10]}")

spec = parse_query_to_spec("give me recipes using asafoetida", requested_mode="find")
print("\nParsed spec:")
print(f"  Mode: {spec.mode}")
print(f"  Include: {spec.ingredients_to_include}")
print(f"  Avoid: {spec.ingredients_to_avoid}")

cand_ids = ing_idx.find_candidate_recipe_ids(
    required_ingredients=spec.ingredients_to_include,
    avoided_ingredients=spec.ingredients_to_avoid
)
print(f"find_candidate_recipe_ids result count: {len(cand_ids)}")

ret_docs, ret_indices = retrieve_hybrid_rrf(
    query_spec=spec,
    df=df,
    embed_model=re_engine._embed_model,
    faiss_index=re_engine._faiss_index,
    bm25_model=re_engine._bm25_model,
    ingredient_index=ing_idx,
    top_k=5
)
print(f"\nretrieve_hybrid_rrf returned {len(ret_docs)} docs:")
for i, d in enumerate(ret_docs, 1):
    print(f"  {i}. {d.get('title')} (score={d.get('rrf_score')})")
    print(f"     Ingredients: {str(d.get('ingredients'))[:120]}")
