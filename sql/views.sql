-- Nettoyage (si tu relances)
DROP VIEW IF EXISTS v_kpi_global;
DROP VIEW IF EXISTS v_sales_profit_by_category;
DROP VIEW IF EXISTS v_customer_profit;
DROP VIEW IF EXISTS v_product_profit_by_category;
DROP VIEW IF EXISTS v_monthly_sales_profit;
DROP VIEW IF EXISTS v_discount_impact;
DROP VIEW IF EXISTS v_shipdays_vs_profit;
DROP VIEW IF EXISTS v_sales_profit_by_ship_mode;
DROP VIEW IF EXISTS v_kpi_loss_orders;
DROP VIEW IF EXISTS v_kpi_unprofitable_customers;
DROP VIEW IF EXISTS v_kpi_monthly;
DROP VIEW IF EXISTS v_kpi_region;
DROP VIEW IF EXISTS v_neg_profit_by_category;
DROP VIEW IF EXISTS v_neg_profit_by_region;
DROP VIEW IF EXISTS v_neg_profit_by_discount_band;



-- 1) KPI global

CREATE VIEW v_kpi_global AS
SELECT
  -- KPI principaux
  ROUND(SUM(oi.Sales), 2)  AS total_sales,
  ROUND(SUM(oi.Profit), 2) AS total_profit,
  ROUND(
    SUM(oi.Profit) * 100.0 / NULLIF(SUM(oi.Sales), 0),
    2
  ) AS profit_margin_pct,

  -- KPI bonus
  COUNT(DISTINCT oi.Order_ID) AS total_orders,
  ROUND(
    SUM(oi.Sales) / NULLIF(COUNT(DISTINCT oi.Order_ID), 0),
    2
  ) AS avg_order_value,
  ROUND(
    SUM(oi.Profit) / NULLIF(COUNT(DISTINCT oi.Order_ID), 0),
    2
  ) AS avg_profit_per_order

FROM order_items oi;

-- 2) Ventes & profit par catégorie
CREATE VIEW v_sales_profit_by_category AS
SELECT
  dc.Category,
  ROUND(SUM(oi.Sales), 2) AS sales,
  ROUND(SUM(oi.Profit), 2) AS profit,
  ROUND(SUM(oi.Profit) * 100.0 / NULLIF(SUM(oi.Sales),0), 2) AS margin_pct
FROM order_items oi
JOIN products p ON p.Product_ID = oi.Product_ID
JOIN dim_category dc ON dc.category_id = p.category_id
GROUP BY dc.Category;

-- 3) Profit par client (sans LIMIT/ORDER dans la vue)
CREATE VIEW v_customer_profit AS
SELECT
  c.Customer_ID,
  c.Customer_Name,
  ROUND(SUM(oi.Sales), 2) AS sales,
  ROUND(SUM(oi.Profit), 2) AS profit
FROM order_items oi
JOIN orders o ON o.Order_ID = oi.Order_ID
JOIN customers c ON c.Customer_ID = o.Customer_ID
GROUP BY c.Customer_ID, c.Customer_Name;

-- 8) Profit par produit + catégorie (sans LIMIT/ORDER dans la vue)
CREATE VIEW v_product_profit_by_category AS
SELECT
  p.Product_ID,
  p.Product_Name,
  dc.Category,
  dc.Sub_Category,
  ROUND(SUM(oi.Profit), 2) AS profit
FROM order_items oi
JOIN products p ON p.Product_ID = oi.Product_ID
JOIN dim_category dc ON dc.category_id = p.category_id
GROUP BY p.Product_ID, p.Product_Name, dc.Category, dc.Sub_Category;

-- 4) Tendance mensuelle ventes/profit
CREATE VIEW v_monthly_sales_profit AS
SELECT
  substr(o.Order_Date, 1, 7) AS month,
  ROUND(SUM(oi.Sales), 2) AS sales,
  ROUND(SUM(oi.Profit), 2) AS profit
FROM order_items oi
JOIN orders o ON o.Order_ID = oi.Order_ID
WHERE o.Order_Date IS NOT NULL
GROUP BY month;

-- 5) Impact des remises (Discount bands)
CREATE VIEW v_discount_impact AS
WITH b AS (
  SELECT
    CASE
      WHEN Discount IS NULL THEN 'NULL'
      WHEN Discount = 0 THEN '0%'
      WHEN Discount <= 0.10 THEN '0-10%'
      WHEN Discount <= 0.20 THEN '10-20%'
      WHEN Discount <= 0.30 THEN '20-30%'
      ELSE '30%+'
    END AS discount_band,
    Sales, Profit
  FROM order_items
)
SELECT
  discount_band,
  COUNT(*) AS n,
  ROUND(AVG(Sales), 2) AS avg_sales,
  ROUND(AVG(Profit), 2) AS avg_profit
FROM b
GROUP BY discount_band;

-- 6) Délai livraison vs profit (résumé global)
CREATE VIEW v_shipdays_vs_profit AS
SELECT
  ROUND(AVG(o.Number_of_days), 2) AS avg_ship_days,
  ROUND(AVG(oi.Profit), 2) AS avg_profit_per_item
FROM order_items oi
JOIN orders o ON o.Order_ID = oi.Order_ID
WHERE o.Number_of_days IS NOT NULL;

-- 7) Ship Mode: ventes & profit
CREATE VIEW v_sales_profit_by_ship_mode AS
SELECT
  sm.Ship_Mode,
  ROUND(SUM(oi.Sales), 2) AS sales,
  ROUND(SUM(oi.Profit), 2) AS profit
FROM order_items oi
JOIN orders o ON o.Order_ID = oi.Order_ID
JOIN dim_ship_mode sm ON sm.ship_mode_id = o.ship_mode_id
GROUP BY sm.Ship_Mode;

--8) Taux de commandes déficitaires
CREATE VIEW v_kpi_loss_orders AS
SELECT
  COUNT(*) AS total_orders,
  SUM(CASE WHEN order_profit < 0 THEN 1 ELSE 0 END) AS loss_orders,
  ROUND(
    SUM(CASE WHEN order_profit < 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
    2
  ) AS loss_order_rate_pct
FROM (
  SELECT
    o.Order_ID,
    SUM(oi.Profit) AS order_profit
  FROM orders o
  JOIN order_items oi ON oi.Order_ID = o.Order_ID
  GROUP BY o.Order_ID
);

--9)% de clients non rentables
CREATE VIEW v_kpi_unprofitable_customers AS
SELECT
  COUNT(*) AS total_customers,
  SUM(CASE WHEN customer_profit < 0 THEN 1 ELSE 0 END) AS unprofitable_customers,
  ROUND(
    SUM(CASE WHEN customer_profit < 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
    2
  ) AS unprofitable_customer_pct
FROM (
  SELECT
    c.Customer_ID,
    SUM(oi.Profit) AS customer_profit
  FROM customers c
  JOIN orders o ON o.Customer_ID = c.Customer_ID
  JOIN order_items oi ON oi.Order_ID = o.Order_ID
  GROUP BY c.Customer_ID
);

--10)KPI par mois
CREATE VIEW v_kpi_monthly AS
SELECT
  substr(o.Order_Date, 1, 7) AS month,
  COUNT(DISTINCT o.Order_ID) AS orders,
  ROUND(SUM(oi.Sales), 2) AS sales,
  ROUND(SUM(oi.Profit), 2) AS profit,
  ROUND(
    SUM(oi.Profit) * 100.0 / NULLIF(SUM(oi.Sales), 0),
    2
  ) AS margin_pct
FROM orders o
JOIN order_items oi ON oi.Order_ID = o.Order_ID
GROUP BY month
ORDER BY month;

--11)KPI par région
CREATE VIEW v_kpi_region AS
SELECT
  g.Region,
  ROUND(SUM(oi.Sales), 2) AS sales,
  ROUND(SUM(oi.Profit), 2) AS profit,
  ROUND(
    SUM(oi.Profit) * 100.0 / NULLIF(SUM(oi.Sales), 0),
    2
  ) AS margin_pct
FROM order_items oi
JOIN orders o ON o.Order_ID = oi.Order_ID
JOIN customers c ON c.Customer_ID = o.Customer_ID
JOIN dim_geo g ON g.geo_id = c.geo_id
GROUP BY g.Region;


--12)profit négatif par catégorie
CREATE VIEW IF NOT EXISTS v_neg_profit_by_category AS
SELECT
  dc.Category,
  COUNT(*) AS n_items,
  SUM(CASE WHEN oi.Profit < 0 THEN 1 ELSE 0 END) AS n_neg,
  ROUND(100.0 * SUM(CASE WHEN oi.Profit < 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_neg,
  ROUND(SUM(oi.Sales), 2) AS sales,
  ROUND(SUM(oi.Profit), 2) AS profit
FROM order_items oi
JOIN products p ON p.Product_ID = oi.Product_ID
JOIN dim_category dc ON dc.category_id = p.category_id
GROUP BY dc.Category
ORDER BY pct_neg DESC;

-- 13)profit négatif par région
CREATE VIEW IF NOT EXISTS v_neg_profit_by_region AS
SELECT
  g.Region,
  COUNT(*) AS n_items,
  SUM(CASE WHEN oi.Profit < 0 THEN 1 ELSE 0 END) AS n_neg,
  ROUND(100.0 * SUM(CASE WHEN oi.Profit < 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_neg,
  ROUND(SUM(oi.Sales), 2) AS sales,
  ROUND(SUM(oi.Profit), 2) AS profit
FROM order_items oi
JOIN orders o ON o.Order_ID = oi.Order_ID
JOIN customers c ON c.Customer_ID = o.Customer_ID
JOIN dim_geo g ON g.geo_id = c.geo_id
GROUP BY g.Region
ORDER BY pct_neg DESC;

--14) profit négatif par tranche de remise
CREATE VIEW IF NOT EXISTS v_neg_profit_by_discount_band AS
WITH b AS (
  SELECT
    CASE
      WHEN Discount IS NULL THEN 'NULL'
      WHEN Discount = 0 THEN '0%'
      WHEN Discount <= 0.10 THEN '0-10%'
      WHEN Discount <= 0.20 THEN '10-20%'
      WHEN Discount <= 0.30 THEN '20-30%'
      ELSE '30%+'
    END AS band,
    Profit
  FROM order_items
)
SELECT
  band,
  COUNT(*) AS n_items,
  SUM(CASE WHEN Profit < 0 THEN 1 ELSE 0 END) AS n_neg,
  ROUND(100.0 * SUM(CASE WHEN Profit < 0 THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_neg,
  ROUND(AVG(Profit), 2) AS avg_profit
FROM b
GROUP BY band
ORDER BY n_items DESC;