import sqlite3

DB = "data/superstore_clean.db"
con = sqlite3.connect(DB)
cur = con.cursor()

checks = []

def check(name, sql, expected=0):
    val = cur.execute(sql).fetchone()[0]
    ok = (val == expected)
    checks.append((name, val, expected, ok))

# Orphelins (devrait être 0)
check("Orphan order_items -> orders",
      """SELECT COUNT(*) FROM order_items oi
         LEFT JOIN orders o ON o.Order_ID = oi.Order_ID
         WHERE o.Order_ID IS NULL;""")

check("Orphan order_items -> products",
      """SELECT COUNT(*) FROM order_items oi
         LEFT JOIN products p ON p.Product_ID = oi.Product_ID
         WHERE p.Product_ID IS NULL;""")

# Discounts invalides (devrait être 0)
check("Bad discount (<0 or >1)",
      """SELECT COUNT(*) FROM order_items
         WHERE Discount IS NOT NULL AND (Discount < 0 OR Discount > 1);""")

# Row_ID NULL dans order_items (devrait être 0)
check("Null Row_ID in order_items",
      """SELECT COUNT(*) FROM order_items WHERE Row_ID IS NULL;""")

# Résultats
print("\n=== DATA QUALITY CHECKS ===")
failed = 0
for name, val, exp, ok in checks:
    status = "PASS " if ok else "FAIL "
    print(f"{status} | {name}: {val} (expected {exp})")
    if not ok:
        failed += 1

con.close()

if failed:
    raise SystemExit(f"\n {failed} checks failed.")
print("\n All checks passed.")