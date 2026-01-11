from __future__ import annotations

import numpy as np
import pandas as pd


def add_growth_and_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().sort_values(["state", "district", "month"]).reset_index(drop=True)

    for c in ["enrol_total", "demo_total", "bio_total"]:
        out[f"{c}_mom"] = out.groupby(["state", "district"])[c].pct_change().fillna(0).clip(-1, 5)

    # Robust anomaly score: deviation from rolling median
    for c in ["enrol_total", "demo_total", "bio_total"]:
        med = out.groupby(["state", "district"])[c].transform(lambda s: s.rolling(6, min_periods=2).median())
        mad = out.groupby(["state", "district"])[c].transform(
            lambda s: (s - s.rolling(6, min_periods=2).median()).abs().rolling(6, min_periods=2).median()
        )
        mad = mad.replace(0, np.nan)
        out[f"{c}_anomaly"] = ((out[c] - med).abs() / (1.4826 * mad)).fillna(0.0)

    out["anomaly_max"] = out[["enrol_total_anomaly", "demo_total_anomaly", "bio_total_anomaly"]].max(axis=1)
    out["anomaly_flag"] = out["anomaly_max"] >= 3.5
    return out
