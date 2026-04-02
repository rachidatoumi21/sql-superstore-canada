import sqlite3
import pandas as pd

CSV_PATH = "data/raw/SuperstoreDataset.csv"
DB_PATH  = "data/superstore.db"

# 1) Lire le CSV
df = pd.read_csv(CSV_PATH, low_memory=False)

# 2) Nettoyer noms de colonnes (espaces -> _)
df.columns = [c.strip().replace(" ", "_").replace("-", "_") for c in df.columns]

# 3) mieux convertir les dates
for col in ["Order_Date", "Ship_Date"]:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")

# 4) Créer SQLite + table brute
con = sqlite3.connect(DB_PATH)
df.to_sql("sales_raw", con, if_exists="replace", index=False)

cur = con.cursor()
n = cur.execute("SELECT COUNT(*) FROM sales_raw;").fetchone()[0]
print(" Base créée :", DB_PATH)
print(" Lignes dans sales_raw :", n)

# aperçu colonnes
cols = cur.execute("PRAGMA table_info(sales_raw);").fetchall()
print("\nColonnes dans sales_raw :")
for c in cols:
    print("-", c[1])

con.close()
