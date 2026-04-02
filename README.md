# Superstore Canada — Analyse SQL (SQLite) + EDA Python

Projet portfolio d’analyse de données : construction d’une base **SQLite** à partir d’un CSV, **normalisation** (modèle relationnel), création de **vues SQL (KPI)**, export en CSV et **visualisations Python** (dashboard + tendances).  
Objectif : démontrer un workflow complet *données → modèle → analyse → insights*.

---

##  Objectifs du projet
- Importer un dataset de ventes dans **SQLite** (`sales_raw`)
- Construire un modèle relationnel “portfolio++” (dimensions + faits)
- Créer des **vues KPI** réutilisables pour l’analyse
- Exporter les vues en CSV et produire des graphiques en Python
- Mettre en évidence des **insights business** (marge, promos, rentabilité)

---

##  Données (résumé)
- Source : dataset “Real Canadian Superstore (Canada)” (CSV)
- Volume importé :
  - `sales_raw` : **51 292** lignes
  - `order_items` : **51 290** lignes
  - `orders` : **25 035** commandes
  - `customers` : **1 590** clients
  - `products` : **10 292** produits

---

##  Modèle de données (SQLite)

### Tables
- `sales_raw` : table brute importée depuis le CSV  
- `orders` : 1 ligne par commande
- `order_items` : lignes d’items par commande (produits)
- `customers`, `products` : dimensions principales

### Dimensions (portfolio++)
- `dim_geo`, `dim_segment`, `dim_category`, `dim_ship_mode`, `dim_order_priority`, `dim_date`

### Vues SQL (KPI)
- `v_kpi_global` : ventes/profit/marge + panier moyen, etc.
- `v_kpi_monthly` : KPI par mois
- `v_kpi_region` : KPI par région
- `v_sales_profit_by_category`, `v_sales_profit_by_ship_mode`, etc.

---

##  Data Quality (audit)

### Constats clés
- **2 lignes vides / corrompues** détectées dans `sales_raw` (`Row_ID` NULL + champs clés NULL).  
  Elles n’impactent pas `order_items` (filtré sur `Row_ID IS NOT NULL`).
- Cohérence globale des volumes : `orders` < `order_items` (normal : une commande contient plusieurs items).

### Indicateurs “qualité / business”
- **Profit négatif** : ~**24.46%** des items ont un profit < 0  
  → important pour la stratégie de promotions et le contrôle des coûts.
- **Promotions agressives** : ~**20.2%** des items ont une remise > 30%  
  → probable lien avec la hausse de profits négatifs.
- **Outliers** :
  - `Sales max` ≈ **22 638**
  - `Shipping_Cost max` ≈ **933**
  → transactions exceptionnelles à investiguer (gros paniers / livraisons coûteuses).

---

## 📊 Visualisations (exemples)

Les graphiques sont générés depuis `data/exports/` et sauvegardés dans `reports/figures/`.

- Dashboard KPI (tuiles “PowerBI style”)  
  `reports/figures/01_kpi_global_tiles.png`
- Tendance mensuelle : ventes & profit  
  `reports/figures/02_monthly_sales_profit.png`
- Tendance mensuelle : marge (%)  
  `reports/figures/03_monthly_margin_pct.png`
- Profit par catégorie / région / mode de livraison  
  `reports/figures/05_profit_by_category.png`  
  `reports/figures/09_profit_by_region.png`  
  `reports/figures/07_sales_profit_by_ship_mode.png`

> Option : afficher les images directement dans le README :
> - `![Dashboard KPI](reports/figures/01_kpi_global_tiles.png)`
> - `![Monthly Sales vs Profit](reports/figures/02_monthly_sales_profit.png)`
> - `![Monthly Margin](reports/figures/03_monthly_margin_pct.png)`

---

## 💡 Insights business (résultats)
1) **Rentabilité : une part significative des ventes est non rentable**  
   Environ **1 item sur 4** présente un profit négatif → opportunité d’optimiser la stratégie de prix/promos et/ou les coûts logistiques.

2) **Promotions élevées : forte présence de remises > 30%**  
   Une proportion importante des transactions est fortement remisée (≈ **20%**).  
   À analyser : impact des “discount bands” sur la marge et la probabilité d’être déficitaire.

3) **Croissance vs qualité de profit**  
   Les ventes peuvent croître alors que le profit reste plus volatil : croissance ≠ rentabilité.  
   Recommandation : suivre mensuellement la marge (%) et pas seulement le chiffre d’affaires.

4) **Régions / catégories : volume ≠ marge**  
   Certaines régions/catégories peuvent générer beaucoup de ventes avec une marge faible : utile pour prioriser les actions (mix produit, promotions, logistique).

5) **Transactions exceptionnelles (outliers)**  
   Quelques ventes/livraisons très élevées suggèrent des cas particuliers (B2B, expédition spéciale). À traiter séparément pour éviter de biaiser certaines moyennes.

---

## ▶️ Reproduire le projet (pipeline)

### 1) Import CSV → DB brute

python db/build_db.py

### 2) Normalisation (tables + dimensions + index)
python db/02_normalize.py

### 3) Générer une DB “clean”
python scripts/build_clean_db.py

### 4) Créer les vues SQL
Exécuter sql/views.sql dans DBeaver

### 5) Exporter les vues en CSV
Exporter vers data/exports/ (ex : kpi_global.csv, kpi_monthly.csv, etc.)

### 6) Tests automatiques Data Quality (PASS/FAIL) 

 python scripts/dq_checks.py

### 7) Générer les graphiques
python scripts/make_charts.py


# Outils utilisés

. SQLite + DBeaver
. Python : pandas, matplotlib, seaborn
. VS Code





