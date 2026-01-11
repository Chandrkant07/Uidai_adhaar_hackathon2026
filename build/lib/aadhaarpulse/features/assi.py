from __future__ import annotations

import numpy as np
import pandas as pd


def _zscore(x: pd.Series) -> pd.Series:
    mu = x.mean()
    sd = x.std(ddof=0)
    if sd == 0 or np.isnan(sd):
        return pd.Series(np.zeros(len(x)), index=x.index)
    return (x - mu) / sd


def compute_assi(panel: pd.DataFrame) -> pd.DataFrame:
    """Compute Aadhaar Service Stress Index (ASSI) at district-month.

    ASSI is a composite score capturing: growth shock, update load, and biometric pressure.

    We keep the formula transparent and tunable.
    """

    df = panel.copy().sort_values(["state", "district", "month"]).reset_index(drop=True)

    # Growth rates (month-over-month), robust with +1 smoothing
    df["enrol_mom"] = df.groupby(["state", "district"])["enrol_total"].pct_change().fillna(0)
    df["demo_per_enrol"] = (df["demo_total"] + 1) / (df["enrol_total"] + 1)
    df["bio_per_enrol"] = (df["bio_total"] + 1) / (df["enrol_total"] + 1)

    # Proxy for "failure / rework": unusually high updates per enrolment
    # (Without explicit failure counts, we treat repeated corrections as friction.)
    df["friction_proxy"] = df["demo_per_enrol"]

    # Standardize components globally (national comparability)
    z_enrol_growth = _zscore(df["enrol_mom"].clip(-2, 2))
    z_update_load = _zscore(np.log1p(df["demo_total"] + df["bio_total"]))
    z_bio_pressure = _zscore(df["bio_per_enrol"].clip(0, df["bio_per_enrol"].quantile(0.99)))
    z_friction = _zscore(df["friction_proxy"].clip(0, df["friction_proxy"].quantile(0.99)))

    # Final index: weighted sum (weights can be calibrated)
    df["ASSI"] = 0.35 * z_enrol_growth + 0.35 * z_update_load + 0.20 * z_bio_pressure + 0.10 * z_friction

    # Scale to 0–100 for governance dashboards
    mn, mx = df["ASSI"].min(), df["ASSI"].max()
    if mx == mn:
        df["ASSI_0_100"] = 50.0
    else:
        df["ASSI_0_100"] = 100 * (df["ASSI"] - mn) / (mx - mn)

    return df


def assi_formula_markdown() -> str:
    return (
        "ASSI is defined at district $d$ and month $t$ as:\n\n"
        "$$\\mathrm{ASSI}_{d,t} = 0.35\\,Z(\\Delta \\mathrm{Enrol}_{d,t}) + 0.35\\,Z(\\log(1+\\mathrm{Updates}_{d,t})) "
        "+ 0.20\\,Z(\\mathrm{BioPerEnrol}_{d,t}) + 0.10\\,Z(\\mathrm{FrictionProxy}_{d,t})$$\n\n"
        "Where:\n"
        "- $\\Delta \\mathrm{Enrol}_{d,t}$ is month-over-month enrolment growth (smoothed, clipped).\n"
        "- $\\mathrm{Updates}_{d,t} = \\mathrm{DemoUpdates}_{d,t} + \\mathrm{BioUpdates}_{d,t}$.\n"
        "- $\\mathrm{BioPerEnrol}_{d,t} = (\\mathrm{BioUpdates}+1)/(\\mathrm{Enrol}+1)$.\n"
        "- $\\mathrm{FrictionProxy}_{d,t} = (\\mathrm{DemoUpdates}+1)/(\\mathrm{Enrol}+1)$ (proxy for repeat corrections).\n"
        "- $Z(\\cdot)$ is a national z-score for comparability.\n"
    )
