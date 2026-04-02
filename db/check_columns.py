import pandas as pd

CSV_PATH = "data/raw/SuperstoreDataset.csv"  # <-- change le nom si différent

df = pd.read_csv(CSV_PATH, low_memory=False)
print("Lignes, colonnes:", df.shape)
print("Colonnes:")
for c in df.columns:
    print("-", c)
print("\nAperçu:")
print(df.head(3))
