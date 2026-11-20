"""Period averages and point values behind Tables 1, 2 and 4 and the figures quoted in the text.

Reads macro.csv (assembled by assemble_data.py) and the outputs of ssm_decomposition.py
and germany_nx.py in results/, and prints every number that appears in the tables and in
the running text, so that each can be checked against its source.
"""
import numpy as np
import pandas as pd

m = pd.read_csv("macro.csv", index_col=0)
nifa = pd.read_csv("results/nifa_periods.csv", index_col=0)
ssm = pd.read_csv("results/ssm_periods_all_variants.csv")
ssm_a = pd.read_csv("results/ssm_annual_baseline.csv", index_col=0)
de = pd.read_csv("results/germany_periods.csv", index_col=0)

P = {"2000-08": (2000, 2008), "2009-19": (2009, 2019), "2020-25": (2020, 2025)}
P_SA = {"2000-08": (2000, 2008), "2009-19": (2009, 2019), "2020-23": (2020, 2023)}  # sector accounts to 2023


def avg(col, periods=P, scale=1.0):
    return {k: scale * m.loc[a:b, col].mean() for k, (a, b) in periods.items()}


def pct_gdp(col):
    return {k: (m.loc[a:b, col] / (m.loc[a:b, "gdp_nominal"] * 1000) * 100).mean() for k, (a, b) in P_SA.items()}


def show(label, d, nd=1):
    print(f"{label:70s}", "  ".join(f"{k}: {v:.{nd}f}" for k, v in d.items()))


print("=== Table 1: macroeconomic policy regime ===")
m["real_short_rate"] = m["irs"] - m["cpi"]
show("Real short-term rate (irs - cpi)", avg("real_short_rate"))
show("Nominal unit labour cost growth", avg("nulc_growth"))
show("General government net lending, sector accounts (% GDP)", pct_gdp("b9_gov"))
show("Cyclically adjusted primary balance, OECD (% potential GDP)", avg("capb_oecd"), 2)
m["d_capb"] = m["capb_oecd"].diff()
m["d_gap"] = m["output_gap"].diff()
for k, (a, b) in P.items():
    sub = m.loc[a:b]
    same = int(((sub["d_capb"] > 0) & (sub["d_gap"] > 0) | (sub["d_capb"] < 0) & (sub["d_gap"] < 0)).sum())
    neg = int((sub["output_gap"] < 0).sum())
    print(f"  {k}: balance and gap move together in {same} of {len(sub)} years; output gap negative in {neg} of {len(sub)} years")
m["pub_inv_pct"] = m["p51_gov"] / (m["gdp_nominal"] * 1000) * 100
show("Public investment (% GDP)", avg("pub_inv_pct"))
show("Export share (% GDP)", avg("export_share"), 0)
show("Import share (% GDP)", avg("import_share"), 0)
show("REER (2010 = 100)", avg("reer"), 0)

print("\n=== Table 2: regime indicators ===")
print(nifa.round(2).to_string())
show("Balance of goods and services, BoP (% GDP)", avg("gs_balance_pct"))
show("Current account, BoP (% GDP)", avg("ca_pct"))
m["b9_priv"] = m["b9_hh"] + m["b9_nfc"] + m["b9_fc"]
show("Private sector balance (% GDP)", pct_gdp("b9_priv"))
show("  households", pct_gdp("b9_hh"))
show("  corporations (non-financial + financial)", {k: v for k, v in
     zip(P_SA, [pct_gdp("b9_nfc")[k] + pct_gdp("b9_fc")[k] for k in P_SA])})
show("Government balance (% GDP)", pct_gdp("b9_gov"))
show("Rest of the world balance (% GDP)", pct_gdp("b9_row"))
m["ca_ca_gap"] = m["ca_pct"] + (m["b9_row"] / (m["gdp_nominal"] * 1000) * 100)
print("  BoP current account less sector-accounts external balance, average 2000-2023: "
      f"{m.loc[2000:2023, 'ca_ca_gap'].mean():.1f} pp")
m["pop_growth"] = 100 * m["population"].pct_change()
m["gdp_pc"] = m["Y"] / m["population"]
m["gdp_pc_growth"] = 100 * m["gdp_pc"].pct_change()
show("Real GDP per capita growth", avg("gdp_pc_growth"))
show("Population growth", avg("pop_growth"))
show("Net migration (thousand)", avg("net_migration", scale=1 / 1000), 0)
show("CPI inflation", avg("cpi"))
for k, (a, b) in P.items():
    sub = nifa.loc[k] if k in nifa.index else None
print("  Domestic demand share of growth (C + G + I, excluding inventories) and incl. inventories:")
for k in nifa.index:
    r = nifa.loc[k]
    dom = r["private_consumption"] + r["public_consumption"] + r["investment"]
    print(f"    {k}: excl. inventories {100 * dom / r['gdp_growth']:.0f}%, incl. inventories "
          f"{100 * (dom + r['inventories']) / r['gdp_growth']:.0f}%, net exports {100 * r['net_exports'] / r['gdp_growth']:.0f}%")

print("\n=== Table 3 point values (baseline) ===")
for y in (2001, 2008, 2019, 2025):
    r = ssm_a.loc[y]
    print(f"  {y}: c = {r['c']:.3f}, beta = {r['b']:.3f}, m = {r['m']:.3f}, mu = {r['mu']:.3f}")

print("\n=== Table 4: Germany, same method ===")
print(de.round(2).to_string())

print("\n=== Text: sections 1, 3.3, 3.4, 5.2 ===")
print(f"  Real GDP 2016-2025: {100 * (m.loc[2025, 'Y'] / m.loc[2016, 'Y'] - 1):.1f}%")
print(f"  Current account average 2016-2025: {m.loc[2016:2025, 'ca_pct'].mean():.1f}% of GDP")
print(f"  Population 2000: {m.loc[2000, 'population'] / 1e6:.2f} m; 2024: {m.loc[2024, 'population'] / 1e6:.2f} m")
print(f"  REER change 2007-2011: {100 * (m.loc[2011, 'reer'] / m.loc[2007, 'reer'] - 1):.0f}%; 2014-2015: "
      f"{100 * (m.loc[2015, 'reer'] / m.loc[2014, 'reer'] - 1):.0f}%; 2000-2025: {100 * (m.loc[2025, 'reer'] / m.loc[2000, 'reer'] - 1):.0f}%; "
      f"2008-2015: {100 * (m.loc[2015, 'reer'] / m.loc[2008, 'reer'] - 1):.0f}%")
m["labour_share"] = m["d1_tot"] / (m["gdp_nominal"] * 1000) * 100
print(f"  Compensation of employees, % GDP: 2000 {m.loc[2000, 'labour_share']:.1f}; 2019 {m.loc[2019, 'labour_share']:.1f}; 2023 {m.loc[2023, 'labour_share']:.1f}")
print(f"  PWT labour share: 1998 {m.loc[1998, 'labsh_pwt']:.2f}; 2019 {m.loc[2019, 'labsh_pwt']:.2f}")
print(f"  S80/S20: 2007 {m.loc[2007, 's80_s20']:.1f}; 2023 {m.loc[2023, 's80_s20']:.1f}")
show("Household gross saving rate (% disposable income)", {k: m.loc[a:b, "hh_saving_rate"].mean() for k, (a, b) in P_SA.items()}, 0)
print(f"  Household credit, % GDP: 2001 {m.loc[2001, 'hh_credit_pct']:.0f}; max {m['hh_credit_pct'].max():.0f} in {int(m['hh_credit_pct'].idxmax())}; 2025 {m.loc[2025, 'hh_credit_pct']:.0f}")
print(f"  Household GFCF, CHF bn: min {m['p51_hh'].min() / 1000:.1f} ({int(m['p51_hh'].idxmin())}), max {m['p51_hh'].max() / 1000:.1f} ({int(m['p51_hh'].idxmax())}); "
      f"total GFCF 1998 {m.loc[1998, 'p51_tot'] / 1000:.0f}, 2023 {m.loc[2023, 'p51_tot'] / 1000:.1f}")
print(f"  Cumulative real GDP growth 2000-2025: {100 * (m.loc[2025, 'Y'] / m.loc[2000, 'Y'] - 1):.1f}%; per capita: {100 * (m.loc[2025, 'gdp_pc'] / m.loc[2000, 'gdp_pc'] - 1):.1f}%")
