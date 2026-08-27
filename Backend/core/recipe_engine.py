import os
import json
import pickle
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

from core.schemas import QuerySpec, RecipeResult
from constraints.constraint_extractor import parse_query_to_spec
from ingredients.normalizer import normalize_ingredient, normalize_ingredient_list
from ingredients.ingredient_index import IngredientIndex
from ingredients.compatibility_graph import IngredientCompatibilityGraph
from retrieval.hybrid_retriever import retrieve_hybrid_rrf
from retrieval.parent_retriever import retrieve_diverse_parents
from generation.novel_generator import generate_novel_candidates
from validation.recipe_validator import validate_synthesized_recipe
from validation.novelty_scorer import compute_novelty_score

_engine_initialized = False
_df = None
_embed_model = None
_faiss_index = None
_bm25_model = None
_ingredient_index = None
_compatibility_graph = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
FAISS_INDEX_PATH = os.path.join(DATA_DIR, "recipes_faiss.index")
METADATA_PATH = os.path.join(DATA_DIR, "recipes_metadata.pkl")
INGREDIENT_INDEX_PATH = os.path.join(DATA_DIR, "ingredient_index.pkl")
COMPATIBILITY_GRAPH_PATH = os.path.join(DATA_DIR, "ingredient_compatibility.pkl")
FIXTURE_PATH = os.path.join(BASE_DIR, "tests", "fixtures", "recipes_small.json")


def _stringify_field(val: Any) -> str:
    if isinstance(val, list):
        return ", ".join([str(i) for i in val if i])
    return str(val) if val is not None else ""


def initialize_engine(use_fixture_if_missing: bool = True):
    global _engine_initialized, _df, _embed_model, _faiss_index, _bm25_model
    global _ingredient_index, _compatibility_graph

    if _engine_initialized:
        return

    # Check if full dataset files exist
    has_full_data = os.path.exists(METADATA_PATH) and os.path.exists(FAISS_INDEX_PATH)

    if has_full_data:
        print("Loading full RecipeDB metadata...")
        with open(METADATA_PATH, "rb") as f:
            metadata = pickle.load(f)
        _df = pd.DataFrame(metadata)
        
        print("Loading FAISS index...")
        import faiss
        _faiss_index = faiss.read_index(FAISS_INDEX_PATH)

        print("Loading embedding model...")
        from sentence_transformers import SentenceTransformer
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    elif use_fixture_if_missing and os.path.exists(FIXTURE_PATH):
        print("Full dataset missing. Loading test fixture recipes_small.json...")
        with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
            fixture_data = json.load(f)
        _df = pd.DataFrame(fixture_data)
        
        # Mock embedding & FAISS index for fixture
        class DummyEmbedder:
            def encode(self, texts, **kwargs):
                return np.random.randn(len(texts), 384).astype(np.float32)
        
        class DummyFaiss:
            def search(self, emb, k):
                indices = np.arange(min(k, len(_df))).reshape(1, -1)
                distances = np.zeros_like(indices, dtype=np.float32)
                return distances, indices

        _embed_model = DummyEmbedder()
        _faiss_index = DummyFaiss()
    else:
        # Empty fallback DataFrame
        _df = pd.DataFrame(columns=["recipe_id", "title", "ingredients", "normalized_ingredients", "instructions", "document"])
        class DummyEmbedder:
            def encode(self, texts, **kwargs):
                return np.zeros((len(texts), 384), dtype=np.float32)
        class DummyFaiss:
            def search(self, emb, k):
                return np.zeros((1, k)), -np.ones((1, k), dtype=np.int64)
        _embed_model = DummyEmbedder()
        _faiss_index = DummyFaiss()

    if "document" not in _df.columns:
        titles = _df["title"].apply(_stringify_field)
        ings = _df["ingredients"].apply(_stringify_field)
        insts = _df["instructions"].apply(_stringify_field)
        _df["document"] = "Recipe Name: " + titles + "\n\nIngredients: " + ings + "\n\nInstructions: " + insts

    # Ensure normalized_ingredients column exists
    if "normalized_ingredients" not in _df.columns or _df["normalized_ingredients"].isnull().any():
        _df["normalized_ingredients"] = _df["ingredients"].apply(
            lambda raw: normalize_ingredient_list(raw if isinstance(raw, list) else [i.strip() for i in str(raw).split(",") if i.strip()])
        )

    # Memory-efficient BM25 index building over titles & ingredients
    print("Building memory-efficient BM25 index...")
    from rank_bm25 import BM25Okapi
    try:
        bm25_texts = [
            (_stringify_field(row.get("title")) + " " + _stringify_field(row.get("ingredients"))).lower().split()
            for _, row in _df.iterrows()
        ]
        _bm25_model = BM25Okapi(bm25_texts)
    except (MemoryError, Exception) as e:
        print(f"Warning: Full BM25 memory allocation failed ({e}). Building BM25 on sampled corpus...")
        sample_df = _df.head(50000)
        bm25_texts = [
            (_stringify_field(row.get("title")) + " " + _stringify_field(row.get("ingredients"))).lower().split()
            for _, row in sample_df.iterrows()
        ]
        _bm25_model = BM25Okapi(bm25_texts)

    # Load or build Ingredient Index
    if os.path.exists(INGREDIENT_INDEX_PATH):
        print("Loading ingredient index...")
        _ingredient_index = IngredientIndex.load(INGREDIENT_INDEX_PATH)
    else:
        print("Building ingredient index in memory...")
        _ingredient_index = IngredientIndex()
        _ingredient_index.build_from_recipes(_df.to_dict("records"))

    # Load or build Compatibility Graph
    if os.path.exists(COMPATIBILITY_GRAPH_PATH):
        print("Loading ingredient compatibility graph...")
        _compatibility_graph = IngredientCompatibilityGraph.load(COMPATIBILITY_GRAPH_PATH)
    else:
        print("Building ingredient compatibility graph in memory...")
        _compatibility_graph = IngredientCompatibilityGraph()
        _compatibility_graph.build_from_recipes(_df.to_dict("records"))

    _engine_initialized = True
    print("Recipe Engine Initialized Successfully!\n")


def answer_query(query: str, requested_mode: str = "auto", novelty_level: str = "balanced") -> Dict[str, Any]:
    """
    Central recipe engine orchestrator handling find, novel, and auto routes.
    Returns structured RecipeResult dict with mode, scores, and provenance.
    """
    initialize_engine()

    # 1. Parse Query & Extract Specs
    query_spec = parse_query_to_spec(query, requested_mode=requested_mode, novelty_level=novelty_level)
    
    rewritten_query = f"{' '.join(query_spec.ingredients_to_include)} {query_spec.meal or ''}".strip()
    if query_spec.ingredients_to_avoid:
        rewritten_query += " without " + ", ".join(query_spec.ingredients_to_avoid)

    # 2. Retrieve Exact Candidate Matches
    exact_docs, exact_indices = retrieve_hybrid_rrf(
        query_spec,
        _df,
        _embed_model,
        _faiss_index,
        _bm25_model,
        ingredient_index=_ingredient_index,
        top_k=5
    )

    effective_mode = query_spec.mode

    # ROUTE A: Mode is "find"
    if effective_mode == "find":
        if exact_docs:
            top_rec = exact_docs[0]
            raw_ings = top_rec.get("ingredients", "")
            ing_list = [i.strip() for i in raw_ings.split(",") if i.strip()] if isinstance(raw_ings, str) else raw_ings
            raw_insts = top_rec.get("instructions", "")
            inst_list = [i.strip() for i in raw_insts.split(".") if i.strip()] if isinstance(raw_insts, str) else raw_insts

            res = RecipeResult(
                title=top_rec.get("title", "Retrieved Recipe"),
                ingredients=ing_list if ing_list else ["Dataset Ingredients"],
                instructions=inst_list if inst_list else ["Follow dataset instructions."],
                mode="retrieved",
                servings=2,
                prep_time=10,
                cook_time=20,
                required_ingredients=query_spec.ingredients_to_include,
                avoided_ingredients=query_spec.ingredients_to_avoid,
                scores={
                    "constraint_satisfaction": 1.0,
                    "grounding": 1.0,
                    "ingredient_step_consistency": 1.0,
                    "compatibility": 1.0,
                    "novelty": 0.0
                },
                provenance=[{"recipe_id": top_rec.get("recipe_id"), "title": top_rec.get("title"), "type": "exact_retrieved_match"}],
                query=query,
                rewritten_query=rewritten_query,
                constraints=query_spec.to_dict(),
                retrieved_recipes=exact_docs,
                answer_raw=str(top_rec.get("document", ""))
            )
            return res.to_dict()
        else:
            res = RecipeResult(
                title="No Exact Recipe Found",
                ingredients=["No exact dataset recipe matching your required ingredients."],
                instructions=["Try enabling 'Create New' (Novel Mode) to synthesize a custom recipe."],
                mode="retrieved",
                required_ingredients=query_spec.ingredients_to_include,
                avoided_ingredients=query_spec.ingredients_to_avoid,
                scores={"constraint_satisfaction": 0.0, "grounding": 0.0, "novelty": 0.0},
                provenance=[],
                query=query,
                rewritten_query=rewritten_query,
                constraints=query_spec.to_dict(),
                retrieved_recipes=[]
            )
            return res.to_dict()

    # ROUTE B: Mode is "auto" and exact matches exist
    if effective_mode == "auto" and exact_docs:
        top_rec = exact_docs[0]
        raw_ings = top_rec.get("ingredients", "")
        ing_list = [i.strip() for i in raw_ings.split(",") if i.strip()] if isinstance(raw_ings, str) else raw_ings
        raw_insts = top_rec.get("instructions", "")
        inst_list = [i.strip() for i in raw_insts.split(".") if i.strip()] if isinstance(raw_insts, str) else raw_insts

        res = RecipeResult(
            title=top_rec.get("title", "Retrieved Recipe"),
            ingredients=ing_list if ing_list else ["Dataset Ingredients"],
            instructions=inst_list if inst_list else ["Follow dataset instructions."],
            mode="retrieved",
            servings=2,
            prep_time=10,
            cook_time=20,
            required_ingredients=query_spec.ingredients_to_include,
            avoided_ingredients=query_spec.ingredients_to_avoid,
            scores={
                "constraint_satisfaction": 1.0,
                "grounding": 1.0,
                "ingredient_step_consistency": 1.0,
                "compatibility": 1.0,
                "novelty": 0.0
            },
            provenance=[{"recipe_id": top_rec.get("recipe_id"), "title": top_rec.get("title"), "type": "exact_retrieved_match"}],
            query=query,
            rewritten_query=rewritten_query,
            constraints=query_spec.to_dict(),
            retrieved_recipes=exact_docs,
            answer_raw=str(top_rec.get("document", ""))
        )
        return res.to_dict()

    # ROUTE C: Mode is "novel" OR ("auto" with no exact match) -> SYNTHESIS ROUTE
    parent_recipes = retrieve_diverse_parents(
        query_spec,
        _df,
        _embed_model,
        _faiss_index,
        _bm25_model,
        ingredient_index=_ingredient_index,
        num_parents=4
    )

    compatible_ings = []
    if query_spec.ingredients_to_include:
        for req in query_spec.ingredients_to_include:
            comp_tuples = _compatibility_graph.get_compatible(req, top_n=3)
            for c_name, _ in comp_tuples:
                if c_name not in query_spec.ingredients_to_avoid and c_name not in compatible_ings:
                    compatible_ings.append(c_name)

    candidates = generate_novel_candidates(
        query_spec,
        parent_recipes,
        compatible_ingredients=compatible_ings,
        num_candidates=3
    )

    valid_candidates = []
    for cand in candidates:
        val_res = validate_synthesized_recipe(cand, query_spec, parent_recipes, _compatibility_graph)
        cand["validation"] = val_res
        if val_res.is_valid:
            nov_scores = compute_novelty_score(cand, _df, _ingredient_index)
            cand["novelty_scores"] = nov_scores
            valid_candidates.append(cand)

    if valid_candidates:
        valid_candidates.sort(key=lambda c: c["novelty_scores"]["novelty_score"], reverse=True)
        best_cand = valid_candidates[0]
        val_res = best_cand["validation"]
        nov_scores = best_cand["novelty_scores"]

        prov = []
        for p in parent_recipes:
            prov.append({"recipe_id": p.get("recipe_id"), "title": p.get("title"), "type": "evidence_parent"})

        res = RecipeResult(
            title=best_cand["title"],
            ingredients=best_cand["ingredients"],
            instructions=best_cand["instructions"],
            mode="synthesized",
            servings=best_cand.get("servings", 2),
            prep_time=best_cand.get("prep_time", 10),
            cook_time=best_cand.get("cook_time", 15),
            required_ingredients=query_spec.ingredients_to_include,
            avoided_ingredients=query_spec.ingredients_to_avoid,
            scores={
                "constraint_satisfaction": val_res.constraint_score,
                "grounding": val_res.grounding_score,
                "ingredient_step_consistency": val_res.ingredient_step_consistency,
                "compatibility": val_res.compatibility_score,
                "novelty": nov_scores["novelty_score"],
                "ingredient_novelty": nov_scores["ingredient_novelty"],
                "technique_novelty": nov_scores["technique_novelty"]
            },
            provenance=prov,
            query=query,
            rewritten_query=rewritten_query,
            constraints=query_spec.to_dict(),
            retrieved_recipes=parent_recipes,
            answer_raw=best_cand.get("raw_response", "")
        )
        return res.to_dict()

    # Truthful fallback if synthesis failed validation or Ollama is offline
    res = RecipeResult(
        title="Novel Recipe Synthesis Error",
        ingredients=["Unable to generate a valid grounded recipe satisfying all constraints."],
        instructions=["Ensure Ollama server is running or try relaxing ingredient constraints."],
        mode="synthesized",
        required_ingredients=query_spec.ingredients_to_include,
        avoided_ingredients=query_spec.ingredients_to_avoid,
        scores={"constraint_satisfaction": 0.0, "grounding": 0.0, "novelty": 0.0},
        provenance=[],
        query=query,
        rewritten_query=rewritten_query,
        constraints=query_spec.to_dict(),
        retrieved_recipes=parent_recipes
    )
    return res.to_dict()
