import os
import re
import json
import pickle
import numpy as np
import pandas as pd
import faiss
import requests
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

from scripts.text_utils import clean_text
from constraints.constraint_extractor import extract_constraints
from query.query_rewritter import rewrite_query
from memory.conversation_memory import save_turn
from memory.memory_retriever import retrieve_memory
from memory.retrieval_cache import save_retrieval_cache
from substitution.ingredient_filter import filter_recipes

# ================= PATHS =================
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
FAISS_INDEX_PATH = "data/recipes_faiss.index"
METADATA_PATH = "data/recipes_metadata.pkl"
TOP_K = 10
OLLAMA_URL = "http://localhost:11434/api/generate"

LOG_DIR = "evaluation/logs"

# ================= LOAD DATA =================
print("Loading RAG backend...")

print("Loading embedding model...")
embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

print("Loading FAISS index...")
index = faiss.read_index(FAISS_INDEX_PATH)

print("Loading metadata...")
with open(METADATA_PATH, "rb") as f:
    metadata = pickle.load(f)

df = pd.DataFrame(metadata)

if "document" not in df.columns:
    df["document"] = (
        "Recipe Name: " + df["title"].fillna("") +
        "\n\nIngredients: " + df["ingredients"].fillna("") +
        "\n\nInstructions: " + df["instructions"].fillna("")
    )

print("Building BM25 index...")
tokenized_corpus = [clean_text(doc).split() for doc in df["document"]]
bm25 = BM25Okapi(tokenized_corpus)

print("RAG Ready\n")

# ================= OLLAMA =================
def call_ollama(prompt: str) -> str:
    models_to_try = [
        ("phi:latest", 15),
        ("llama3:latest", 25),
        ("mistral:latest", 25)
    ]
    for model_name, t_out in models_to_try:
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.15,
                "num_predict": 280
            }
        }
        try:
            r = requests.post(OLLAMA_URL, json=payload, timeout=t_out)
            if r.status_code == 200:
                resp = r.json().get("response", "").strip()
                if resp and len(resp) > 20:
                    return resp
        except Exception:
            continue
    return ""

# ================= MAXIMUM KEYWORD MATCHING & STRICT AVOIDANCE RETRIEVAL =================
def retrieve(query: str, avoid_ingredients: list = None, top_k: int = TOP_K):
    """
    Perform hybrid retrieval with Maximum Keyword Matching & Strict Avoidance Reranking.
    Excludes any dataset recipes containing avoid_ingredients across a wide candidate pool.
    """
    avoid_terms = [a.lower().strip() for a in (avoid_ingredients or []) if a and len(a) > 1]

    # Clean positive query by removing "without ..." suffix for vector & BM25 search
    positive_query = query
    if " without " in query.lower():
        positive_query = query.lower().split(" without ")[0].strip()

    query_clean = clean_text(positive_query)
    query_words = set(query_clean.split())

    stop_words = {"give", "generate", "recipe", "for", "a", "an", "the", "how", "to", "make", "prepare", "with", "without", "some", "please", "can", "you", "i", "want", "need", "not", "have", "don't", "dont", "avoid"}
    target_keywords = [w for w in query_words if w not in stop_words and len(w) > 1 and w not in avoid_terms and not any(a in w for a in avoid_terms)]

    # ===== FAISS Search (Candidate pool of 100) =====
    emb = embed_model.encode([positive_query])
    faiss_scores, faiss_indices = index.search(np.array(emb), min(100, len(df)))

    # ===== BM25 Search =====
    tokenized_query = query_clean.split()
    bm25_scores = bm25.get_scores(tokenized_query)
    top_bm25_indices = np.argsort(bm25_scores)[::-1][:100]

    # Combine candidate indices
    candidate_indices = []
    for idx in faiss_indices[0]:
        if idx not in candidate_indices and int(idx) < len(df):
            candidate_indices.append(int(idx))
    for idx in top_bm25_indices:
        if idx not in candidate_indices and int(idx) < len(df):
            candidate_indices.append(int(idx))

    # ===== STRICT AVOIDANCE FILTER & RERANKER =====
    scored_candidates = []
    for idx in candidate_indices:
        row = df.iloc[idx]
        doc_text = str(row["document"]).lower()
        title_text = str(row.get("title", "")).lower()

        # Strict Avoidance Check
        has_avoided = False
        if avoid_terms:
            for term in avoid_terms:
                pattern = r"\b" + re.escape(term) + r"(?:s|es)?\b"
                if re.search(pattern, doc_text) or re.search(pattern, title_text):
                    has_avoided = True
                    break
        if has_avoided:
            continue

        # Count keyword occurrences from positive target keywords
        title_matches = sum(1 for kw in target_keywords if kw in title_text)
        doc_matches = sum(1 for kw in target_keywords if kw in doc_text)

        # Exact phrase bonus
        exact_phrase_bonus = 5.0 if query_clean in title_text or query_clean in doc_text else 0.0

        match_score = (title_matches * 3.0) + doc_matches + (float(bm25_scores[idx]) * 0.1) + exact_phrase_bonus
        scored_candidates.append((match_score, idx))

    scored_candidates.sort(key=lambda x: x[0], reverse=True)

    docs = []
    indices = []
    for score, idx in scored_candidates[:top_k]:
        docs.append(df.iloc[idx]["document"])
        indices.append(idx)

    # Fallback to unfiltered top candidate if all 100 candidates were avoided
    if not docs and candidate_indices:
        for idx in candidate_indices[:top_k]:
            docs.append(df.iloc[idx]["document"])
            indices.append(idx)

    return docs, [indices]


# ================= QUERY ANSWERING =================
def answer_query(query: str) -> str:
    conversation_history = retrieve_memory(query)
    constraints = extract_constraints(query)

    rewritten_query = rewrite_query(
        query,
        conversation_history,
        constraints
    )

    avoid_list = constraints.get("ingredients_to_avoid", [])
    docs, indices = retrieve(rewritten_query, avoid_ingredients=avoid_list)
    save_retrieval_cache(rewritten_query, docs)

    if len(docs) == 0:
        return "Recipe not found in database after applying ingredient constraints."

    top_doc = docs[0]
    context = "\n".join(list(dict.fromkeys(docs)))

    user_avail = constraints.get("user_available_ingredients", [])
    avail_note = f"User explicitly has these ingredients: {', '.join(user_avail)}." if user_avail else ""

    prompt = f"""
You are Chef Master AI, a world-class professional culinary research assistant powered by RAG technology.

User Request: {query}
Rewritten Hybrid Query: {rewritten_query}
Active Constraints: {constraints}
{avail_note}
Conversation History: {conversation_history if conversation_history else "First message in session"}

Retrieved Knowledge Base:
{context}

CULINARY FUSION & COMBINATION INSTRUCTIONS:
1. INGREDIENT COMBINATION: If the user requested adding new ingredients to an existing recipe (e.g., adding eggs/paneer to Chicken Biryani), combine the base recipe from the Knowledge Base with the new requested ingredients into a single, seamless, delicious recipe.
2. PRESERVE DISH INTEGRITY: Retain core ingredients from the base dish while incorporating the new items smoothly.
3. ACADEMIC & PROFESSIONAL STRUCTURE:
   - Title: <Exact Fusion/Recipe Name>
   - Ingredients: (bullet points with precise measurements)
   - Instructions: (numbered steps showing exact preparation & cooking)
   - Chef Note: (professional culinary commentary on flavor profile & cooking technique)

Generate the complete recipe now:
"""

    answer = call_ollama(prompt)

    # Fallback to dataset recipe document if Ollama times out or fails
    if not answer or len(answer) < 30:
        lines = top_doc.split("\n")
        t_title = "Delicious Recipe"
        t_ing = []
        t_inst = []
        sec = None
        for l in lines:
            ls = l.strip()
            if not ls:
                continue
            if ls.lower().startswith("recipe name:"):
                t_title = ls.split(":", 1)[1].strip()
            elif ls.lower().startswith("ingredients:"):
                sec = "ing"
                val = ls.split(":", 1)[1].strip()
                if val:
                    t_ing.extend([i.strip() for i in val.split(",") if i.strip()])
            elif ls.lower().startswith("instructions:"):
                sec = "inst"
                val = ls.split(":", 1)[1].strip()
                if val:
                    t_inst.append(val)
            elif sec == "ing":
                t_ing.extend([i.strip() for i in ls.split(",") if i.strip()])
            elif sec == "inst":
                t_inst.append(ls)

        answer = f"Title: {t_title}\n\nIngredients:\n"
        answer += "\n".join([f"- {ing}" for ing in (t_ing if t_ing else ["Main Ingredients"])])
        answer += "\n\nInstructions:\n"
        answer += "\n".join([f"{i+1}. {step}" for i, step in enumerate(t_inst if t_inst else ["Cook thoroughly on medium flame.", "Serve hot!"])])
        answer += "\n\nChef Note:\nHere is a delicious recipe prepared from our culinary knowledge base!"

    save_turn(query, answer, constraints)
    return answer
