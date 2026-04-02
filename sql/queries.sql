-- 1) KPI global
SELECT
  ROUND(SUM(oi.Sales), 2)  AS total_sales,
  ROUND(SUM(oi.Profit), 2) AS total_profit,
  ROUND(SUM(oi.Profit) * 100.0 / NULLIF(SUM(oi.Sales),0), 2) AS profit_margin_pct
FROM order_items oi;

-- 2) Ventes & profit par catégorie
SELECT
  dc.Category,
  ROUND(SUM(oi.Sales), 2) AS sales,
  ROUND(SUM(oi.Profit), 2) AS profit,
  ROUND(SUM(oi.Profit) * 100.0 / NULLIF(SUM(oi.Sales),0), 2) AS margin_pct
FROM order_items oi
JOIN products p ON p.Product_ID = oi.Product_ID
JOIN dim_category dc ON dc.category_id = p.category_id
GROUP BY dc.Category
ORDER BY sales DESC;

-- 3) Top 10 clients par profit
SELECT
  c.Customer_ID,
  c.Customer_Name,
  ROUND(SUM(oi.Sales), 2) AS sales,
  ROUND(SUM(oi.Profit), 2) AS profit
FROM order_items oi
JOIN customers c ON c.Customer_ID = (
    SELECT o.Customer_ID FROM orders o WHERE o.Order_ID = oi.Order_ID
)
GROUP BY c.Customer_ID, c.Customer_Name
ORDER BY profit DESC
LIMIT 10;

-- 4) Tendance mensuelle des ventes (Order_Date)
SELECT
  substr(o.Order_Date, 1, 7) AS month,
  ROUND(SUM(oi.Sales), 2) AS sales,
  ROUND(SUM(oi.Profit), 2) AS profit
FROM order_items oi
JOIN orders o ON o.Order_ID = oi.Order_ID
WHERE o.Order_Date IS NOT NULL
GROUP BY month
ORDER BY month;

-- 5) Impact des remises (Discount bands)
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
GROUP BY discount_band
ORDER BY n DESC;

-- 6) Délai de livraison vs profit (Ship days)
SELECT
  ROUND(AVG(o.Number_of_days), 2) AS avg_ship_days,
  ROUND(AVG(oi.Profit), 2) AS avg_profit_per_item
FROM order_items oi
JOIN orders o ON o.Order_ID = oi.Order_ID
WHERE o.Number_of_days IS NOT NULL;

-- 7) Ship Mode: ventes & profit
SELECT
  sm.Ship_Mode,
  ROUND(SUM(oi.Sales), 2) AS sales,
  ROUND(SUM(oi.Profit), 2) AS profit
FROM order_items oi
JOIN orders o ON o.Order_ID = oi.Order_ID
JOIN dim_ship_mode sm ON sm.ship_mode_id = o.ship_mode_id
GROUP BY sm.Ship_Mode
ORDER BY sales DESC;

-- 8) Top 10 produits par profit (avec catégorie)
SELECT
  p.Product_ID,
  p.Product_Name,
  dc.Category,
  dc.Sub_Category,
  ROUND(SUM(oi.Profit), 2) AS profit
FROM order_items oi
JOIN products p ON p.Product_ID = oi.Product_ID
JOIN dim_category dc ON dc.category_id = p.category_id
GROUP BY p.Product_ID, p.Product_Name, dc.Category, dc.Sub_Category
ORDER BY profit DESC
LIMIT 10;
