import sqlite3

DB_PATH = "data/superstore.db"
con = sqlite3.connect(DB_PATH)
cur = con.cursor()

# 1) Customers
cur.execute("DROP TABLE IF EXISTS customers;")
cur.execute("""
CREATE TABLE customers AS
SELECT DISTINCT
  Customer_ID,
  Customer_Name,
  Segment,
  City,
  State,
  Country,
  Region
FROM sales_raw
WHERE Customer_ID IS NOT NULL;
""")

# 2) Products
cur.execute("DROP TABLE IF EXISTS products;")
cur.execute("""
CREATE TABLE products AS
SELECT DISTINCT
  Product_ID,
  Product_Name,
  Category,
  Sub_Category,
  unit_cost
FROM sales_raw
WHERE Product_ID IS NOT NULL;
""")

# 3) Orders (une ligne par commande)
cur.execute("DROP TABLE IF EXISTS orders;")
cur.execute("""
CREATE TABLE orders AS
SELECT DISTINCT
  Order_ID,
  Order_Date,
  Ship_Date,
  Number_of_days,
  Ship_Mode,
  Order_Priority,
  Shipping_Cost
FROM sales_raw
WHERE Order_ID IS NOT NULL;
""")

# 4) Order items (lignes de commande)
cur.execute("DROP TABLE IF EXISTS order_items;")
cur.execute("""
CREATE TABLE order_items AS
SELECT
  Row_ID,
  Order_ID,
  Customer_ID,
  Product_ID,
  Sales,
  Quantity,
  Discount,
  Profit,
  Profit_per_unit,
  Unit_Sales,
  Unit_shipping_cost
FROM sales_raw;
""")

con.commit()

# Vérifier tailles
for t in ["customers", "products", "orders", "order_items"]:
    n = cur.execute(f"SELECT COUNT(*) FROM {t};").fetchone()[0]
    print(f"✅ {t}: {n} lignes")

con.close()
