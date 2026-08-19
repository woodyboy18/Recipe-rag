"""Runtime configuration. All paths are absolute so the backend never depends
on the working directory (the old code relied on os.chdir())."""
import os

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BACKEND_ROOT, "data")
MEMORY_DIR = os.path.join(BACKEND_ROOT, "memory")

DATASET_PATH = os.path.join(DATA_DIR, "RecipeDB3_ID_ING_INS.csv")
FAISS_INDEX_PATH = os.path.join(DATA_DIR, "recipes_faiss.index")
METADATA_PATH = os.path.join(DATA_DIR, "recipes_metadata.pkl")

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ---- Ollama LLM -----------------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "phi:latest"          # installed; "llama3:latest" is the upgrade path
OLLAMA_TIMEOUT = 180
OLLAMA_OPTIONS = {
    "temperature": 0.2,
    "num_predict": 300,
    "top_p": 0.9,
    "keep_alive": "5m",              # keep model warm between queries (CPU latency win)
}

# ---- Hybrid retrieval -----------------------------------------------------
TOP_K_FAISS = 60                     # candidate pool per stage
TOP_K_BM25 = 60
RRF_K = 60                           # RRF constant (higher = rank matters less)
RETRIEVAL_TOP_K = 20                 # fused docs returned to the UI
RERANK = False                       # optional cross-encoder reranking (off by default)

# ---- Prompt / LLM context ------------------------------------------------
PROMPT_DOCS = 4                      # docs placed in the LLM context (phi ctx=2048)
PROMPT_DOC_MAX_CHARS = 900
CONVERSATION_MAX_TURNS = 2
CONVERSATION_MAX_CHARS = 500
