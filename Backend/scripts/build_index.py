import pandas as pd
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# ================= CONFIG =================
DATA_PATH = "Backend/data/Recipedb_kk.csv"

FAISS_INDEX_PATH = "Backend/data/recipes_faiss.index"
METADATA_PATH = "Backend/data/recipes_metadata.pkl"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 128   

# ================= LOAD CSV =================
print("Loading dataset...")
df = pd.read_csv(DATA_PATH)

# ================= SELECT + CLEAN =================
df = df[
    ["Recipe_ID", "Recipe Name", "Ingredients", "Directions"]
].fillna("")

# ================= RENAME =================
df = df.rename(columns={
    "Recipe Name": "title",
    "Ingredients": "ingredients",
    "Directions": "instructions"
})

# ================= CLEAN TEXT =================
def clean_text(text):
    return str(text).replace("[", "").replace("]", "").replace("'", "")

df["ingredients"] = df["ingredients"].apply(clean_text)
df["instructions"] = df["instructions"].apply(clean_text)

# ================= BUILD DOCUMENT =================
print("Building documents...")

df["document"] = (
    "Recipe Name: " + df["title"] + "\n\n"
    "Ingredients: " + df["ingredients"] + "\n\n"
    "Instructions: " + df["instructions"]
)

df = df.reset_index(drop=True)

print(f"✅ Total recipes indexed: {len(df)}")

# ================= LOAD EMBEDDING MODEL =================
print("Loading embedding model...")
embed_model = SentenceTransformer(EMBEDDING_MODEL)

embedding_dim = embed_model.get_sentence_embedding_dimension()
index = faiss.IndexFlatL2(embedding_dim)

# ================= BUILD FAISS INDEX =================
print("Creating embeddings and building FAISS index...")

for start in tqdm(range(0, len(df), BATCH_SIZE)):
    texts = df["document"].iloc[start:start + BATCH_SIZE].tolist()

    embeddings = embed_model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=False
    )

    index.add(np.array(embeddings))

# ================= SAVE =================
print("Saving FAISS index...")
faiss.write_index(index, FAISS_INDEX_PATH)

print("Saving metadata...")
df[["title", "ingredients", "instructions", "document"]].to_pickle(METADATA_PATH)

print("\n✅ Indexing completed successfully!")
print(f"FAISS index saved to: {FAISS_INDEX_PATH}")
print(f"Metadata saved to: {METADATA_PATH}")