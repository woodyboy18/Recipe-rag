import os
import json

MEMORY_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(MEMORY_DIR, "retrieval_cache.json")

def save_retrieval_cache(query, docs):
    data = {
        "query": query,
        "recipes": docs
    }

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
