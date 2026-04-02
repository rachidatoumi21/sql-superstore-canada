import sqlite3
from datetime import datetime

DB_PATH = "data/superstore.db"

def to_quarter(m: int) -> int:
    return (m - 1) // 3 + 1

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

# IMPORTANT : activer les clés étrangères dans SQLite
cur.execute("PRAGMA foreign_keys = ON;")

# ---------- DROP (ordre inverse à cause des FK) ----------
tables_to_drop = [
    "order_items",
    "orders",
    "products",
    "customers",
    "dim_date",
    "dim_order_priority",
    "dim_ship_mode",
    "dim_category",
    "dim_segment",
    "dim_geo",
]
for t in tables_to_drop:
    cur.execute(f"DROP TABLE IF EXISTS {t};")

# ---------- DIMENSIONS ----------
cur.execute("""
CREATE TABLE dim_geo (
    geo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    City TEXT,
    State TEXT,
    Country TEXT,
    Region TEXT,
    UNIQUE(City, State, Country, Region)
);
""")

# INSERT OR IGNORE pour éviter tout conflit d'unicité
cur.execute("""
INSERT OR IGNORE INTO dim_geo (City, State, Country, Region)
SELECT DISTINCT City, State, Country, Region
FROM sales_raw
WHERE City IS NOT NULL OR State IS NOT NULL OR Country IS NOT NULL OR Region IS NOT NULL;
""")

cur.execute("""
CREATE TABLE dim_segment (
    segment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    Segment TEXT UNIQUE
);
""")
cur.execute("""
INSERT OR IGNORE INTO dim_segment (Segment)
SELECT DISTINCT Segment
FROM sales_raw
WHERE Segment IS NOT NULL;
""")

cur.execute("""
CREATE TABLE dim_category (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    Category TEXT,
    Sub_Category TEXT,
    UNIQUE(Category, Sub_Category)
);
""")
cur.execute("""
INSERT OR IGNORE INTO dim_category (Category, Sub_Category)
SELECT DISTINCT Category, Sub_Category
FROM sales_raw
WHERE Category IS NOT NULL OR Sub_Category IS NOT NULL;
""")

cur.execute("""
CREATE TABLE dim_ship_mode (
    ship_mode_id INTEGER PRIMARY KEY AUTOINCREMENT,
    Ship_Mode TEXT UNIQUE
);
""")
cur.execute("""
INSERT OR IGNORE INTO dim_ship_mode (Ship_Mode)
SELECT DISTINCT Ship_Mode
FROM sales_raw
WHERE Ship_Mode IS NOT NULL;
""")

cur.execute("""
CREATE TABLE dim_order_priority (
    priority_id INTEGER PRIMARY KEY AUTOINCREMENT,
    Order_Priority TEXT UNIQUE
);
""")
cur.execute("""
INSERT OR IGNORE INTO dim_order_priority (Order_Priority)
SELECT DISTINCT Order_Priority
FROM sales_raw
WHERE Order_Priority IS NOT NULL;
""")

# ---------- DIM DATE ----------
cur.execute("""
CREATE TABLE dim_date (
    date TEXT PRIMARY KEY,      -- 'YYYY-MM-DD'
    year INTEGER,
    month INTEGER,
    day INTEGER,
    quarter INTEGER
);
""")

dates = cur.execute("""
SELECT DISTINCT Order_Date FROM sales_raw WHERE Order_Date IS NOT NULL
UNION
SELECT DISTINCT Ship_Date FROM sales_raw WHERE Ship_Date IS NOT NULL;
""").fetchall()

for (d,) in dates:
    try:
        dt = datetime.strptime(d, "%Y-%m-%d")
        cur.execute("""
            INSERT OR IGNORE INTO dim_date(date, year, month, day, quarter)
            VALUES (?, ?, ?, ?, ?);
        """, (d, dt.year, dt.month, dt.day, to_quarter(dt.month)))
    except:
        pass

# ---------- TABLES ----------
cur.execute("""
CREATE TABLE customers (
    Customer_ID TEXT PRIMARY KEY,
    Customer_Name TEXT,
    segment_id INTEGER,
    geo_id INTEGER,
    FOREIGN KEY(segment_id) REFERENCES dim_segment(segment_id),
    FOREIGN KEY(geo_id) REFERENCES dim_geo(geo_id)
);
""")

# 1 ligne par Customer_ID (évite UNIQUE failed)
cur.execute("""
INSERT INTO customers (Customer_ID, Customer_Name, segment_id, geo_id)
SELECT
    s.Customer_ID,
    MAX(s.Customer_Name) AS Customer_Name,
    MAX(seg.segment_id)  AS segment_id,
    MIN(g.geo_id)        AS geo_id
FROM sales_raw s
LEFT JOIN dim_segment seg ON seg.Segment = s.Segment
LEFT JOIN dim_geo g
  ON COALESCE(g.City,'')    = COALESCE(s.City,'')
 AND COALESCE(g.State,'')   = COALESCE(s.State,'')
 AND COALESCE(g.Country,'') = COALESCE(s.Country,'')
 AND COALESCE(g.Region,'')  = COALESCE(s.Region,'')
WHERE s.Customer_ID IS NOT NULL
GROUP BY s.Customer_ID;
""")

cur.execute("""
CREATE TABLE products (
    Product_ID TEXT PRIMARY KEY,
    Product_Name TEXT,
    category_id INTEGER,
    unit_cost REAL,
    FOREIGN KEY(category_id) REFERENCES dim_category(category_id)
);
""")

# ✅ CORRECTION: 1 ligne par Product_ID (évite UNIQUE failed)
cur.execute("""
INSERT INTO products (Product_ID, Product_Name, category_id, unit_cost)
SELECT
    s.Product_ID,
    MAX(s.Product_Name) AS Product_Name,
    MIN(c.category_id)  AS category_id,
    ROUND(AVG(CAST(s.unit_cost AS REAL)), 2) AS unit_cost
FROM sales_raw s
LEFT JOIN dim_category c
  ON COALESCE(c.Category,'') = COALESCE(s.Category,'')
 AND COALESCE(c.Sub_Category,'') = COALESCE(s.Sub_Category,'')
WHERE s.Product_ID IS NOT NULL
GROUP BY s.Product_ID;
""")

cur.execute("""
CREATE TABLE orders (
    Order_ID TEXT PRIMARY KEY,
    Customer_ID TEXT,
    Order_Date TEXT,
    Ship_Date TEXT,
    ship_mode_id INTEGER,
    priority_id INTEGER,
    Number_of_days REAL,
    Shipping_Cost REAL,
    FOREIGN KEY(Customer_ID) REFERENCES customers(Customer_ID),
    FOREIGN KEY(Order_Date) REFERENCES dim_date(date),
    FOREIGN KEY(Ship_Date) REFERENCES dim_date(date),
    FOREIGN KEY(ship_mode_id) REFERENCES dim_ship_mode(ship_mode_id),
    FOREIGN KEY(priority_id) REFERENCES dim_order_priority(priority_id)
);
""")

# 1 ligne par Order_ID (agrégé)
cur.execute("""
INSERT INTO orders (Order_ID, Customer_ID, Order_Date, Ship_Date, ship_mode_id, priority_id, Number_of_days, Shipping_Cost)
SELECT
    s.Order_ID,
    MAX(s.Customer_ID),
    MAX(s.Order_Date),
    MAX(s.Ship_Date),
    MAX(sm.ship_mode_id),
    MAX(pr.priority_id),
    MAX(s.Number_of_days),
    MAX(s.Shipping_Cost)
FROM sales_raw s
LEFT JOIN dim_ship_mode sm ON sm.Ship_Mode = s.Ship_Mode
LEFT JOIN dim_order_priority pr ON pr.Order_Priority = s.Order_Priority
WHERE s.Order_ID IS NOT NULL
GROUP BY s.Order_ID;
""")

cur.execute("""
CREATE TABLE order_items (
    Row_ID INTEGER PRIMARY KEY,
    Order_ID TEXT,
    Product_ID TEXT,
    Sales REAL,
    Quantity REAL,
    Unit_Sales REAL,
    Discount REAL,
    Profit REAL,
    Profit_per_unit REAL,
    Unit_shipping_cost REAL,
    FOREIGN KEY(Order_ID) REFERENCES orders(Order_ID),
    FOREIGN KEY(Product_ID) REFERENCES products(Product_ID)
);
""")

# ✅ sécuriser Row_ID: DISTINCT pour éviter collision si jamais
cur.execute("""
INSERT INTO order_items (
    Row_ID, Order_ID, Product_ID, Sales, Quantity, Unit_Sales, Discount, Profit, Profit_per_unit, Unit_shipping_cost
)
SELECT DISTINCT
    CAST(Row_ID AS INTEGER),
    Order_ID,
    Product_ID,
    Sales,
    Quantity,
    Unit_Sales,
    Discount,
    Profit,
    Profit_per_unit,
    Unit_shipping_cost
FROM sales_raw
WHERE Row_ID IS NOT NULL;
""")

# ---------- INDEX ----------
cur.execute("CREATE INDEX IF NOT EXISTS idx_items_order ON order_items(Order_ID);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_items_product ON order_items(Product_ID);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(Customer_ID);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_dates ON orders(Order_Date, Ship_Date);")

con.commit()

# ---------- Vérifications ----------
to_check = [
    "dim_geo",
    "dim_segment",
    "dim_category",
    "dim_ship_mode",
    "dim_order_priority",
    "dim_date",
    "customers",
    "products",
    "orders",
    "order_items",
]
for t in to_check:
    n = cur.execute(f"SELECT COUNT(*) FROM {t};").fetchone()[0]
    print(f"✅ {t}: {n} lignes")

con.close()
print("✅ Normalisation portfolio++ terminée.")
