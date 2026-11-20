"""Net-export growth contributions for Germany (Table 4 comparison column).

Source: World Bank WDI (July 2026 vintage), constant LCU (2020 prices):
NY.GDP.MKTP.KN, NE.EXP.GNFS.KN, NE.IMP.GNFS.KN, 1999-2025.
Contribution_t = 100 * (dX_t - dM_t) / Y_{t-1}, averaged over the subperiods.
"""
import pandas as pd

years = list(range(1999, 2026))
gdp = [2747118190000, 2826139680000, 2872379330000, 2865822960000, 2850639790000,
       2883766700000, 2909302030000, 3021795500000, 3109098720000, 3136704480000,
       2962788190000, 3085288750000, 3201232940000, 3216071040000, 3228838700000,
       3299233390000, 3354099840000, 3428635390000, 3524565410000, 3564593760000,
       3599446030000, 3450720000000, 3585643150000, 3650516690000, 3618770060000,
       3600826320000, 3609453120000]
exp = [612321440000, 695206230000, 733273830000, 762701980000, 775256180000,
       861515750000, 918077190000, 1027690290000, 1115569760000, 1132848670000,
       968564010000, 1105175410000, 1192514910000, 1223427960000, 1229232600000,
       1282554240000, 1345055310000, 1371783620000, 1424700290000, 1461148000000,
       1491386090000, 1349915000000, 1487336350000, 1545247700000, 1523379080000,
       1491926060000, 1485311470000]
imp = [593793170000, 656684610000, 661351880000, 640815900000, 672436640000,
       718642590000, 761581460000, 842675240000, 892848370000, 907783630000,
       816421850000, 918284980000, 979542870000, 975459010000, 992844590000,
       1027265690000, 1081989400000, 1122477950000, 1168917270000, 1227608170000,
       1270196990000, 1166817000000, 1275681030000, 1372176790000, 1352924310000,
       1345340000000, 1393646220000]

df = pd.DataFrame({"year": years, "Y": gdp, "X": exp, "M": imp}).set_index("year")
df["growth"] = 100 * df["Y"].pct_change()
df["nx_contrib"] = 100 * (df["X"].diff() - df["M"].diff()) / df["Y"].shift(1)
df["x_contrib"] = 100 * df["X"].diff() / df["Y"].shift(1)
df["m_contrib"] = -100 * df["M"].diff() / df["Y"].shift(1)
df["x_share"] = 100 * df["X"] / df["Y"]

periods = {"2000-08": (2000, 2008), "2009-19": (2009, 2019), "2020-25": (2020, 2025)}
rows = []
for name, (a, b) in periods.items():
    sub = df.loc[a:b]
    rows.append({"period": name, "growth": sub["growth"].mean(),
                 "nx_contrib": sub["nx_contrib"].mean(),
                 "x_contrib": sub["x_contrib"].mean(),
                 "m_contrib": sub["m_contrib"].mean(),
                 "x_share_end": sub["x_share"].iloc[-1],
                 "nx_positive_years": int((sub["nx_contrib"] > 0).sum()),
                 "n_years": len(sub)})
out = pd.DataFrame(rows).set_index("period")
pd.set_option("display.width", 200)
print(df.round(2))
print(out.round(2))
df.to_csv("results/germany_annual.csv")
out.to_csv("results/germany_periods.csv")
