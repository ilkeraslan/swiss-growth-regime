"""Figures 1 to 3 of the manuscript, drawn from macro.csv and results/nifa_annual.csv.

Figure 1: real GDP growth and the growth contributions of private consumption, public
          consumption, gross fixed capital formation, inventories and net exports, 2000-2025.
Figure 2: current account balance, per cent of GDP, with subperiod averages, 2000-2025.
Figure 3: real GDP and real GDP per capita, index 2000 = 100.

Usage: python plot_figures.py  (after assemble_data.py and ssm_decomposition.py)
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": "0.85",
    "grid.linewidth": 0.5,
    "legend.frameon": False,
})

m = pd.read_csv("macro.csv", index_col=0)
n = pd.read_csv("results/nifa_annual.csv", index_col=0).loc[2000:2025]
PERIODS = [("2000–2008", 2000, 2008), ("2009–2019", 2009, 2019), ("2020–2025", 2020, 2025)]

# ---- Figure 1: growth contributions ------------------------------------------------------
fig, ax = plt.subplots(figsize=(6.5, 3.6), dpi=300)
years = n.index.values
components = [
    ("private_consumption", "Private consumption", "0.25"),
    ("public_consumption", "Public consumption", "0.55"),
    ("investment", "Gross fixed capital formation", "0.75"),
    ("inventories", "Inventories and discrepancy", "0.92"),
    ("net_exports", "Net exports", "white"),
]
pos = np.zeros(len(years))
neg = np.zeros(len(years))
for col, label, colour in components:
    vals = n[col].values
    bottom = np.where(vals >= 0, pos, neg)
    ax.bar(years, vals, bottom=bottom, color=colour, edgecolor="black", linewidth=0.4, width=0.8, label=label)
    pos = pos + np.where(vals >= 0, vals, 0)
    neg = neg + np.where(vals < 0, vals, 0)
ax.plot(years, n["gdp_growth"].values, color="black", marker="o", markersize=3, linewidth=1.2, label="Real GDP growth")
ax.axhline(0, color="black", linewidth=0.6)
for _, a, b in PERIODS[1:]:
    ax.axvline(a - 0.5, color="0.4", linewidth=0.6, linestyle="--")
ax.set_ylabel("Per cent and percentage points")
ax.set_xlim(1999.3, 2025.7)
ax.set_xticks(range(2000, 2026, 5))
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=8)
fig.tight_layout()
fig.savefig("results/figure1.png", bbox_inches="tight")
plt.close(fig)

# ---- Figure 2: current account -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6.5, 3.2), dpi=300)
ca = m.loc[2000:2025, "ca_pct"]
ax.bar(ca.index, ca.values, color="0.75", edgecolor="black", linewidth=0.4, width=0.8, label="Current account balance")
for label, a, b in PERIODS:
    avg = ca.loc[a:b].mean()
    ax.hlines(avg, a - 0.4, b + 0.4, color="black", linewidth=1.5)
    ax.text((a + b) / 2, avg + 0.35, f"{label}: {avg:.1f}", ha="center", va="bottom", fontsize=8,
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5))
ax.axhline(0, color="black", linewidth=0.6)
ax.set_ylabel("Per cent of GDP")
ax.set_xlim(1999.3, 2025.7)
ax.set_xticks(range(2000, 2026, 5))
ax.set_ylim(0, max(ca.max() + 2.5, 14))
fig.tight_layout()
fig.savefig("results/figure2.png", bbox_inches="tight")
plt.close(fig)

# ---- Figure 3: GDP and GDP per capita -----------------------------------------------------
fig, ax = plt.subplots(figsize=(6.5, 3.2), dpi=300)
y = m.loc[2000:2025, "Y"]
pc = m.loc[2000:2025, "Y"] / m.loc[2000:2025, "population"]
ax.plot(y.index, 100 * y / y.iloc[0], color="black", linewidth=1.4, label="Real GDP")
ax.plot(pc.index, 100 * pc / pc.iloc[0], color="black", linewidth=1.4, linestyle="--", label="Real GDP per capita")
ax.text(2025.2, 100 * y.iloc[-1] / y.iloc[0], f"{100 * y.iloc[-1] / y.iloc[0]:.0f}", va="center", fontsize=8)
ax.text(2025.2, 100 * pc.iloc[-1] / pc.iloc[0], f"{100 * pc.iloc[-1] / pc.iloc[0]:.0f}", va="center", fontsize=8)
ax.set_ylabel("Index, 2000 = 100")
ax.set_xlim(2000, 2026.5)
ax.set_xticks(range(2000, 2026, 5))
ax.legend(loc="upper left")
fig.tight_layout()
fig.savefig("results/figure3.png", bbox_inches="tight")
plt.close(fig)
print("results/figure1.png, figure2.png, figure3.png written")
