import sys
import os
import pandas as pd

df = pd.read_csv('Backend/data/Recipedb_kk.csv')
asa_exact = df[df['Ingredients'].astype(str).str.contains(r'\basafoetida\b|\bhing\b|\basafetida\b', case=False, na=False)]

print(f"Total REAL asafoetida/hing rows in Recipedb_kk.csv: {len(asa_exact)}")
for idx, r in asa_exact.head(10).iterrows():
    print(f"\nRow {idx}: {r['Recipe Name']}")
    print(f"   Ingredients: {r['Ingredients']}")
