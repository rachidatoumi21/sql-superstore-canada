import os
import shutil
import sqlite3
import pandas as pd

RAW_DB = "data/superstore.db"
CLEAN_DB = "data/superstore_clean.db"

def qdf(conn, sql):
    return pd.read_sql_query(sql, conn)

def main():
    if not os.path.exists(RAW_DB):
        raise FileNotFoundError(f"DB brute introuvable: {RAW_DB}")

    # 1) Copier RAW -> CLEAN (écrase)
    if os.path.exists(CLEAN_DB):
        os.remove(CLEAN_DB)
    shutil.copyfile(RAW_DB, CLEAN_DB)

    con = sqlite3.connect(CLEAN_DB)
    con.execute("PRAGMA foreign_keys = ON;")

    print(" Copie faite ->", CLEAN_DB)

    # 2) Rapport AVANT (audit)
    before = qdf(con, """
    SELECT
      (SELECT COUNT(*) FROM orders) AS n_orders,
      (SELECT COUNT(*) FROM order_items) AS n_items,
      (SELECT COUNT(*) FROM order_items WHERE Sales IS NULL) AS n_null_sales,
      (SELECT COUNT(*) FROM order_items WHERE Profit IS NULL) AS n_null_profit,
      (SELECT COUNT(*) FROM order_items WHERE Discount IS NULL) AS n_null_discount,
      (SELECT COUNT(*) FROM order_items WHERE Discount IS NOT NULL AND (Discount < 0 OR Discount > 1)) AS n_bad_discount,
      (SELECT COUNT(*) FROM order_items WHERE Quantity <= 0) AS n_bad_quantity,
      (SELECT COUNT(*) FROM order_items WHERE Sales < 0) AS n_negative_sales
    """)
    print("\n--- DATA QUALITY (AVANT) ---")
    print(before.to_string(index=False))

    # 3) Nettoyage (dans CLEAN seulement)
    # R1: Discount hors [0,1] -> NULL
    con.execute("""
    UPDATE order_items
    SET Discount = NULL
    WHERE Discount IS NOT NULL AND (Discount < 0 OR Discount > 1);
    """)

    # R2: Sales/Profit NULL -> 0 (simple et stable)
    con.execute("""
    UPDATE order_items
    SET Sales = COALESCE(Sales, 0),
        Profit = COALESCE(Profit, 0);
    """)

    # R3: Dates vides -> NULL
    con.execute("""
    UPDATE orders SET Order_Date = NULL
    WHERE Order_Date IS NOT NULL AND TRIM(Order_Date) = '';
    """)
    con.execute("""
    UPDATE orders SET Ship_Date = NULL
    WHERE Ship_Date IS NOT NULL AND TRIM(Ship_Date) = '';
    """)

    con.commit()

    # 4) Rapport APRÈS
    after = qdf(con, """
    SELECT
      (SELECT COUNT(*) FROM orders) AS n_orders,
      (SELECT COUNT(*) FROM order_items) AS n_items,
      (SELECT COUNT(*) FROM order_items WHERE Sales IS NULL) AS n_null_sales,
      (SELECT COUNT(*) FROM order_items WHERE Profit IS NULL) AS n_null_profit,
      (SELECT COUNT(*) FROM order_items WHERE Discount IS NULL) AS n_null_discount,
      (SELECT COUNT(*) FROM order_items WHERE Discount IS NOT NULL AND (Discount < 0 OR Discount > 1)) AS n_bad_discount,
      (SELECT COUNT(*) FROM order_items WHERE Quantity <= 0) AS n_bad_quantity,
      (SELECT COUNT(*) FROM order_items WHERE Sales < 0) AS n_negative_sales
    """)
    print("\n--- DATA QUALITY (APRÈS) ---")
    print(after.to_string(index=False))

    con.close()
    print("\n DB clean prête :", CLEAN_DB)

if __name__ == "__main__":
    main()
