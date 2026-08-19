import json

CACHE_FILE = "memory/retrieval_cache.json"

def save_retrieval_cache(query, docs):
    data = {
        "query": query,
        "recipes": docs
    }

    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=4)
