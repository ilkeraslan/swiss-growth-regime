"""
Demand-led growth decompositions for the Swiss demand and growth regime paper.

Two decompositions are produced from one annual input file:

1. NIFA growth contributions (Hein 2023; Campana/Hein 2026a, Table 4 format):
   contribution of each demand component k in year t = dK_t / Y_{t-1}.

2. Sraffian supermultiplier (SSM) decomposition following Campana/Hein
   (2026a), equations (3)-(7):

       Y_t = C_a,t + c_t Y_t + I_a,t + b_t Y_t + GC_a,t + GI_a,t + X_a,t - m_t Y_t + E_t
       Z_t = C_a,t + I_a,t + GC_a,t + GI_a,t + X_a,t
       mu_t = 1 / (1 - c_t - b_t + m_t)
       Y_t = mu_t (Z_t + E_t)

   with c_t = (C_t - C_a,t)/Y_t, b_t = (I_t - I_a,t - GI_a,t)/Y_t, m_t = M_t/Y_t.
   Growth decomposition (exact when the components add to GDP):

       Yhat_t = mu_t (dC_a + dI_a + dGC_a + dGI_a + dX_a + dE)_t / Y_{t-1}
                + mu_t (dc_t + db_t - dm_t)

   Campana/Hein write the autonomous terms as mu_t (K_{t-1}/Y_{t-1}) Khat_t,
   which equals mu_t dK_t / Y_{t-1}; the induced terms mu_t (C_i,t-1/Y_{t-1}) chat_t
   equal mu_t dc_t, and likewise for b and m.

Measurement, baseline (Campana/Hein 2026a):
   C_a  = real net flow of household credit: first difference of the BIS stock
          of credit to households, deflated by the GDP deflator.
   I_a  = household-sector share of GFCF x real GFCF.
   GI_a = government-sector share of GFCF x real GFCF.
   GC_a = real government consumption.  X_a = real exports.
   C_i  = C - C_a.  I_i = I - I_a - GI_a.  M = real imports.
   E    = inventories and statistical discrepancy. With chain-linked volumes the
          components do not add exactly; by default E is closed as the residual
          Y - (C + GC + I + X - M) so that the identity holds and the
          contributions sum to measured growth (option --inventories residual).

Swiss variants:
   A: C_a = consumer credit flows only (SNB consumer credit stock), because
      household credit in Switzerland is overwhelmingly mortgage debt.
   B: I_a = real GFCF in dwellings by asset type, because household-sector GFCF
      misses rental housing built by institutional investors.
   AB: both.

Input CSV (annual, one row per year, real series in the same reference-year
prices, nominal stocks in CHF):
   year, Y, C, GC, I, X, M, E, deflator, hh_credit_stock, cons_credit_stock,
   hh_gfcf_share, gov_gfcf_share, dwellings_gfcf
   deflator: GDP deflator index with the real series' reference year = 1.0.
   E may be left blank when --inventories residual is used.

Usage:
   python ssm_decomposition.py data.csv --out results/ \
       --periods 2000-2008 2009-2019 2020-2025 --periods 2000-2007 2011-2019
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

AUTONOMOUS = ["Ca", "Ia", "GCa", "GIa", "Xa"]
INDUCED = ["dc", "db", "dm"]
LABELS = {
    "Ca": "Credit-financed consumption",
    "Ia": "Residential investment",
    "GCa": "Government consumption",
    "GIa": "Government investment",
    "Xa": "Exports",
    "E": "Inventories and discrepancy",
    "dc": "Propensity to consume (induced)",
    "db": "Propensity to invest (induced)",
    "dm": "Propensity to import (induced)",
}


def parse_periods(specs):
    periods = []
    for s in specs:
        a, b = s.split("-")
        periods.append((int(a), int(b)))
    return periods


def close_inventories(df):
    """Set E to the residual so that Y = C + GC + I + X - M + E exactly."""
    out = df.copy()
    out["E"] = out["Y"] - (out["C"] + out["GC"] + out["I"] + out["X"] - out["M"])
    return out


def real_credit_flow(stock, deflator):
    """Real net flow of credit: first difference of the nominal stock, deflated."""
    return stock.diff() / deflator


def build_components(df, variant="baseline"):
    """Return a frame with the autonomous and induced components for one variant."""
    x = df.copy()
    if variant in ("baseline", "B"):
        x["Ca"] = real_credit_flow(x["hh_credit_stock"], x["deflator"])
    elif variant in ("A", "AB"):
        x["Ca"] = real_credit_flow(x["cons_credit_stock"], x["deflator"])
    else:
        raise ValueError(variant)

    if variant in ("baseline", "A"):
        x["Ia"] = x["hh_gfcf_share"] * x["I"]
    else:  # B, AB
        x["Ia"] = x["dwellings_gfcf"]

    x["GIa"] = x["gov_gfcf_share"] * x["I"]
    x["GCa"] = x["GC"]
    x["Xa"] = x["X"]
    x["Ci"] = x["C"] - x["Ca"]
    x["Ii"] = x["I"] - x["Ia"] - x["GIa"]
    x["c"] = x["Ci"] / x["Y"]
    x["b"] = x["Ii"] / x["Y"]
    x["m"] = x["M"] / x["Y"]
    x["mu"] = 1.0 / (1.0 - x["c"] - x["b"] + x["m"])
    x["Z"] = x[AUTONOMOUS].sum(axis=1)
    x["identity_check"] = x["mu"] * (x["Z"] + x["E"]) / x["Y"]  # 1.0 if exact
    return x


def ssm_contributions(x):
    """Annual contributions to real GDP growth in percentage points."""
    y_lag = x["Y"].shift(1)
    out = pd.DataFrame(index=x.index)
    out["year"] = x["year"]
    out["gdp_growth"] = 100 * (x["Y"] / y_lag - 1)
    for k in AUTONOMOUS + ["E"]:
        out[k] = 100 * x["mu"] * x[k].diff() / y_lag
    out["dc"] = 100 * x["mu"] * x["c"].diff()
    out["db"] = 100 * x["mu"] * x["b"].diff()
    out["dm"] = -100 * x["mu"] * x["m"].diff()
    out["sum_contributions"] = out[AUTONOMOUS + ["E"] + INDUCED].sum(axis=1, skipna=False)
    out["residual"] = out["gdp_growth"] - out["sum_contributions"]
    out["mu"] = x["mu"]
    out["c"] = x["c"]
    out["b"] = x["b"]
    out["m"] = x["m"]
    return out


def nifa_contributions(df):
    """Growth contributions of the expenditure components, dK_t / Y_{t-1}."""
    y_lag = df["Y"].shift(1)
    out = pd.DataFrame(index=df.index)
    out["year"] = df["year"]
    out["gdp_growth"] = 100 * (df["Y"] / y_lag - 1)
    out["private_consumption"] = 100 * df["C"].diff() / y_lag
    out["public_consumption"] = 100 * df["GC"].diff() / y_lag
    out["investment"] = 100 * df["I"].diff() / y_lag
    out["inventories"] = 100 * df["E"].diff() / y_lag
    out["exports"] = 100 * df["X"].diff() / y_lag
    out["imports"] = -100 * df["M"].diff() / y_lag
    out["net_exports"] = out["exports"] + out["imports"]
    out["sum_contributions"] = out[
        ["private_consumption", "public_consumption", "investment", "inventories", "net_exports"]
    ].sum(axis=1, skipna=False)
    out["residual"] = out["gdp_growth"] - out["sum_contributions"]
    return out


def period_averages(annual, periods, cols):
    rows = []
    for a, b in periods:
        sel = annual[(annual["year"] >= a) & (annual["year"] <= b)]
        complete = sel.dropna(subset=cols)
        if len(complete) < len(sel):
            dropped = sorted(set(sel["year"]) - set(complete["year"]))
            print(f"warning: period {a}-{b} drops {dropped} (incomplete lags; "
                  f"supply data from two years before the first period)")
        sel = complete
        label = f"{int(sel['year'].min())}-{int(sel['year'].max())}" if len(sel) else f"{a}-{b}"
        row = {"period": label, "n_years": len(sel)}
        for c in cols:
            row[c] = sel[c].mean()
        rows.append(row)
    return pd.DataFrame(rows)


def dominance(avg):
    """Campana/Hein rule: dominant above 50% of autonomous contributions;
    a second component is also dominant at 40% or more."""
    out = avg.copy()
    total = out[AUTONOMOUS].sum(axis=1)
    for k in AUTONOMOUS:
        out[f"share_{k}"] = 100 * out[k] / total
    labels = []
    for _, r in out.iterrows():
        shares = sorted(((r[f"share_{k}"], k) for k in AUTONOMOUS), reverse=True)
        first, second = shares[0], shares[1]
        dom = []
        if first[0] > 50:
            dom.append(LABELS[first[1]])
            if second[0] >= 40:
                dom.append(LABELS[second[1]])
        else:
            dom.append("no dominant component")
        labels.append("; ".join(dom))
    out["dominant"] = labels
    return out


def run(path, out_dir, period_specs, inventories="residual"):
    df = pd.read_csv(path)
    df = df.sort_values("year").reset_index(drop=True)
    required = ["year", "Y", "C", "GC", "I", "X", "M", "deflator", "hh_credit_stock",
                "hh_gfcf_share", "gov_gfcf_share"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        sys.exit(f"missing columns: {missing}")
    if inventories == "residual":
        df = close_inventories(df)
    elif "E" not in df.columns or df["E"].isna().any():
        sys.exit("E must be supplied when --inventories reported is used")

    periods = parse_periods(period_specs)
    os.makedirs(out_dir, exist_ok=True)

    nifa = nifa_contributions(df)
    nifa.to_csv(os.path.join(out_dir, "nifa_annual.csv"), index=False)
    nifa_cols = ["gdp_growth", "private_consumption", "public_consumption", "investment",
                 "inventories", "exports", "imports", "net_exports", "residual"]
    period_averages(nifa, periods, nifa_cols).to_csv(
        os.path.join(out_dir, "nifa_periods.csv"), index=False)

    variants = ["baseline"]
    if "cons_credit_stock" in df.columns and df["cons_credit_stock"].notna().any():
        variants.append("A")
    if "dwellings_gfcf" in df.columns and df["dwellings_gfcf"].notna().any():
        variants.append("B")
    if len(variants) == 3:
        variants.append("AB")

    summary = []
    for v in variants:
        x = build_components(df, v)
        ann = ssm_contributions(x)
        ann.to_csv(os.path.join(out_dir, f"ssm_annual_{v}.csv"), index=False)
        avg = period_averages(ann, periods, ["gdp_growth"] + AUTONOMOUS + ["E"] + INDUCED
                              + ["sum_contributions", "residual", "mu", "c", "b", "m"])
        avg = dominance(avg)
        avg.insert(0, "variant", v)
        avg.to_csv(os.path.join(out_dir, f"ssm_periods_{v}.csv"), index=False)
        summary.append(avg)
        chk = x["identity_check"].dropna()
        print(f"[{v}] identity check mu(Z+E)/Y: min {chk.min():.4f} max {chk.max():.4f}")
    pd.concat(summary).to_csv(os.path.join(out_dir, "ssm_periods_all_variants.csv"), index=False)
    return nifa, summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--out", default="results")
    ap.add_argument("--periods", nargs="+", action="extend",
                    default=None, help="e.g. 2000-2008 2009-2019 2020-2025")
    ap.add_argument("--inventories", choices=["residual", "reported"], default="residual")
    args = ap.parse_args()
    specs = args.periods or ["2000-2008", "2009-2019", "2020-2025", "2000-2007", "2011-2019"]
    run(args.data, args.out, specs, args.inventories)
