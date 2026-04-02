import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import FancyBboxPatch

EXPORTS_DIR = "data/exports"
FIG_DIR = "reports/figures"

os.makedirs(FIG_DIR, exist_ok=True)


# -------------------------
# Helpers lecture & sauvegarde
# -------------------------
def read_csv(filename: str) -> pd.DataFrame:
    path = os.path.join(EXPORTS_DIR, filename)
    return pd.read_csv(path)

def save_fig(name: str):
    out = os.path.join(FIG_DIR, name)
    plt.tight_layout()
    plt.savefig(out, dpi=220, bbox_inches="tight")
    plt.close()
    print(f"✅ {out}")


# -------------------------
# Helpers format KPI
# -------------------------
def fmt_money(x):
    return f"{x:,.2f}".replace(",", " ")

def fmt_int(x):
    return f"{int(round(x)):,}".replace(",", " ")

def fmt_pct(x):
    return f"{x:.2f}%"

def fmt_money_compact(x):
    ax = abs(x)
    if ax >= 1_000_000_000:
        return f"{x/1_000_000_000:.2f}B"
    if ax >= 1_000_000:
        return f"{x/1_000_000:.2f}M"
    if ax >= 1_000:
        return f"{x/1_000:.2f}K"
    return f"{x:.2f}"


# -------------------------
# 1) KPI Tiles (PowerBI-style)
# -------------------------
def _add_tile(ax, x, y, w, h, title, value, subtitle=None):
    tile = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.012,rounding_size=0.02",
        linewidth=1.2,
        edgecolor="#D0D7DE",
        facecolor="white"
    )
    ax.add_patch(tile)

    ax.text(x + 0.04*w, y + 0.78*h, title, fontsize=10.5, color="#57606A", va="center")
    ax.text(x + 0.04*w, y + 0.40*h, value, fontsize=22, fontweight="bold", va="center")

    if subtitle:
        ax.text(x + 0.04*w, y + 0.16*h, subtitle, fontsize=9.5, color="#6E7781", va="center")


def make_kpi_tiles_dashboard():
    df = read_csv("kpi_global.csv")
    r = df.iloc[0]

    total_sales = float(r["total_sales"])
    total_profit = float(r["total_profit"])
    margin_pct = float(r["profit_margin_pct"])
    total_orders = float(r["total_orders"])
    avg_order_value = float(r["avg_order_value"])
    avg_profit_per_order = float(r["avg_profit_per_order"])

    fig = plt.figure(figsize=(12.5, 7.0))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    fig.patch.set_facecolor("white")

    ax.text(0.06, 0.93, "Superstore Canada — Dashboard KPI", fontsize=18, fontweight="bold", va="center")
    ax.text(0.06, 0.90, "Vue synthèse (global) — export CSV depuis vues SQL", fontsize=10.5, color="#57606A", va="center")

    left, right, top, bottom = 0.06, 0.94, 0.84, 0.12
    cols, rows = 3, 2
    gap_x, gap_y = 0.03, 0.05

    tile_w = (right - left - gap_x*(cols-1)) / cols
    tile_h = (top - bottom - gap_y*(rows-1)) / rows

    def pos(c, r_):
        x = left + c*(tile_w + gap_x)
        y = top - (r_+1)*tile_h - r_*gap_y
        return x, y

    x0, y0 = pos(0, 0)
    _add_tile(ax, x0, y0, tile_w, tile_h, "Total ventes",
              f"{fmt_money_compact(total_sales)} $", f"{fmt_money(total_sales)} $")

    x1, y1 = pos(1, 0)
    _add_tile(ax, x1, y1, tile_w, tile_h, "Total profit",
              f"{fmt_money_compact(total_profit)} $", f"{fmt_money(total_profit)} $")

    x2, y2 = pos(2, 0)
    _add_tile(ax, x2, y2, tile_w, tile_h, "Marge", fmt_pct(margin_pct), "Profit / Ventes")

    x3, y3 = pos(0, 1)
    _add_tile(ax, x3, y3, tile_w, tile_h, "Nombre de commandes", fmt_int(total_orders), "Commandes uniques")

    x4, y4 = pos(1, 1)
    _add_tile(ax, x4, y4, tile_w, tile_h, "Panier moyen (AOV)",
              f"{fmt_money(avg_order_value)} $", "Ventes / Commandes")

    x5, y5 = pos(2, 1)
    _add_tile(ax, x5, y5, tile_w, tile_h, "Profit moyen / commande",
              f"{fmt_money(avg_profit_per_order)} $", "Profit / Commandes")

    plt.savefig(os.path.join(FIG_DIR, "01_kpi_global_tiles.png"), dpi=220, bbox_inches="tight")
    plt.close()
    print(f" {os.path.join(FIG_DIR, '01_kpi_global_tiles.png')}")


# -------------------------
# 2) Monthly: ventes/profit + marge
# -------------------------
def make_monthly_charts():
    monthly = read_csv("kpi_monthly.csv")
    monthly["month_dt"] = pd.to_datetime(monthly["month"], format="%Y-%m")
    monthly = monthly.sort_values("month_dt")

    # ventes + profit (ticks lisibles)
    plt.figure(figsize=(12, 5))
    plt.plot(monthly["month_dt"], monthly["sales"], marker="o", label="Ventes")
    plt.plot(monthly["month_dt"], monthly["profit"], marker="o", label="Profit")
    plt.title("Tendance mensuelle : ventes & profit")
    plt.xlabel("Mois")
    plt.ylabel("Montant")
    plt.grid(True, alpha=0.3)
    plt.legend()

    step = 3
    ticks = monthly["month_dt"].iloc[::step]
    plt.xticks(ticks, ticks.dt.strftime("%Y-%m"), rotation=45, ha="right")
    save_fig("02_monthly_sales_profit.png")

    # marge (%)
    monthly["margin_pct"] = pd.to_numeric(monthly["margin_pct"], errors="coerce")
    plt.figure(figsize=(12, 5))
    plt.plot(monthly["month_dt"], monthly["margin_pct"], marker="o")
    plt.title("Tendance mensuelle : marge (%)")
    plt.xlabel("Mois")
    plt.ylabel("Marge (%)")
    plt.grid(True, alpha=0.3)

    ticks = monthly["month_dt"].iloc[::step]
    plt.xticks(ticks, ticks.dt.strftime("%Y-%m"), rotation=45, ha="right")
    save_fig("03_monthly_margin_pct.png")


# -------------------------
# 3) Catégorie
# -------------------------
def make_category_charts():
    cat = read_csv("sales_profit_by_category.csv")
    for c in ["sales", "profit", "margin_pct"]:
        if c in cat.columns:
            cat[c] = pd.to_numeric(cat[c], errors="coerce")
    cat = cat.sort_values("sales", ascending=False)

    plt.figure(figsize=(10, 5))
    sns.barplot(data=cat, x="Category", y="sales")
    plt.title("Ventes par catégorie")
    save_fig("04_sales_by_category.png")

    plt.figure(figsize=(10, 5))
    sns.barplot(data=cat, x="Category", y="profit")
    plt.title("Profit par catégorie")
    save_fig("05_profit_by_category.png")

    plt.figure(figsize=(10, 5))
    sns.barplot(data=cat, x="Category", y="margin_pct")
    plt.title("Marge (%) par catégorie")
    save_fig("06_margin_by_category.png")


# -------------------------
# 4) Ship mode
# -------------------------
def make_ship_mode_chart():
    ship = read_csv("sales_profit_by_ship_mode.csv")
    for c in ["sales", "profit"]:
        if c in ship.columns:
            ship[c] = pd.to_numeric(ship[c], errors="coerce")
    ship = ship.sort_values("sales", ascending=False)

    ship_melt = ship.melt(
        id_vars=["Ship_Mode"],
        value_vars=["sales", "profit"],
        var_name="metric",
        value_name="value"
    )

    plt.figure(figsize=(10, 5))
    sns.barplot(data=ship_melt, x="Ship_Mode", y="value", hue="metric")
    plt.xticks(rotation=20, ha="right")
    plt.title("Ventes & profit par mode de livraison")
    save_fig("07_sales_profit_by_ship_mode.png")


# -------------------------
# 5) Région
# -------------------------
def make_region_charts():
    r = read_csv("kpi_region.csv")
    for c in ["sales", "profit", "margin_pct"]:
        if c in r.columns:
            r[c] = pd.to_numeric(r[c], errors="coerce")
    r = r.sort_values("sales", ascending=False)

    plt.figure(figsize=(10, 5))
    sns.barplot(data=r, x="Region", y="sales")
    plt.xticks(rotation=20, ha="right")
    plt.title("Ventes par région")
    save_fig("08_sales_by_region.png")

    plt.figure(figsize=(10, 5))
    sns.barplot(data=r, x="Region", y="profit")
    plt.xticks(rotation=20, ha="right")
    plt.title("Profit par région")
    save_fig("09_profit_by_region.png")

    plt.figure(figsize=(10, 5))
    sns.barplot(data=r, x="Region", y="margin_pct")
    plt.xticks(rotation=20, ha="right")
    plt.title("Marge (%) par région")
    save_fig("10_margin_by_region.png")


# -------------------------
# MAIN
# -------------------------
def main():
    sns.set_theme(style="whitegrid")  # look propre

    make_kpi_tiles_dashboard()
    make_monthly_charts()
    make_category_charts()
    make_ship_mode_chart()
    make_region_charts()

    print("\n Terminé : toutes les figures sont dans reports/figures/")


if __name__ == "__main__":
    main()
