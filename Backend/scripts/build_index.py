import os
import pandas as pd
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from ingredients.normalizer import normalize_ingredient_list
from ingredients.ingredient_index import IngredientIndex

# ================= CONFIG =================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "Recipedb_kk.csv")
FAISS_INDEX_PATH = os.path.join(BASE_DIR, "data", "recipes_faiss.index")
METADATA_PATH = os.path.join(BASE_DIR, "data", "recipes_metadata.pkl")
INGREDIENT_INDEX_PATH = os.path.join(BASE_DIR, "data", "ingredient_index.pkl")

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 128   

def build_index_main():
    # ================= LOAD CSV =================
    print("Loading dataset...")
    df = pd.read_csv(DATA_PATH)

    # ================= SELECT + CLEAN =================
    df = df[
        ["Recipe_ID", "Recipe Name", "Ingredients", "Directions"]
    ].fillna("")

    # ================= RENAME =================
    df = df.rename(columns={
        "Recipe_ID": "recipe_id",
        "Recipe Name": "title",
        "Ingredients": "ingredients",
        "Directions": "instructions"
    })

    def clean_text(text):
        return str(text).replace("[", "").replace("]", "").replace("'", "")

    df["ingredients"] = df["ingredients"].apply(clean_text)
    df["instructions"] = df["instructions"].apply(clean_text)

    print("Normalizing ingredients...")
    df["normalized_ingredients"] = df["ingredients"].apply(
        lambda ing_str: normalize_ingredient_list([i.strip() for i in ing_str.split(",") if i.strip()])
    )

    # ================= BUILD DOCUMENT =================
    print("Building documents...")
    df["document"] = (
        "Recipe Name: " + df["title"] + "\n\n"
        "Ingredients: " + df["ingredients"] + "\n\n"
        "Instructions: " + df["instructions"]
    )

    df = df.reset_index(drop=True)
    print(f"✅ Total recipes indexed: {len(df)}")

    # ================= BUILD INGREDIENT INDEX =================
    print("Building structured ingredient index...")
    recipes_list = df.to_dict("records")
    ing_index = IngredientIndex()
    ing_index.build_from_recipes(recipes_list)
    ing_index.save(INGREDIENT_INDEX_PATH)
    print(f"✅ Ingredient index saved to: {INGREDIENT_INDEX_PATH}")

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
    df[["recipe_id", "title", "ingredients", "normalized_ingredients", "instructions", "document"]].to_pickle(METADATA_PATH)

    print("\n✅ Indexing completed successfully!")

if __name__ == "__main__":
    build_index_main()