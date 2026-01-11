from __future__ import annotations

import pandas as pd


def build_panel(enrol: pd.DataFrame, demo: pd.DataFrame, bio: pd.DataFrame) -> pd.DataFrame:
    """Unify datasets at district-month level.

    Grain: (state, district, month)

    We aggregate PINs to district to make a stable national panel.
    """

    keys = ["state", "district", "month"]

    e = enrol.groupby(keys, as_index=False).agg(
        enrol_total=("enrol_total", "sum"),
        enrol_age_0_5=("age_0_5", "sum"),
        enrol_age_5_17=("age_5_17", "sum"),
        enrol_age_18p=("age_18_greater", "sum"),
        enrol_pins=("pincode", "nunique"),
        enrol_days=("date", "nunique"),
    )

    d = demo.groupby(keys, as_index=False).agg(
        demo_total=("demo_total", "sum"),
        demo_pins=("pincode", "nunique"),
        demo_days=("date", "nunique"),
    )

    b = bio.groupby(keys, as_index=False).agg(
        bio_total=("bio_total", "sum"),
        bio_pins=("pincode", "nunique"),
        bio_days=("date", "nunique"),
    )

    panel = e.merge(d, on=keys, how="outer").merge(b, on=keys, how="outer")

    # fill missing with zeros for volumes
    for c in [
        "enrol_total",
        "enrol_age_0_5",
        "enrol_age_5_17",
        "enrol_age_18p",
        "demo_total",
        "bio_total",
    ]:
        panel[c] = panel[c].fillna(0).astype("int64")

    for c in ["enrol_pins", "enrol_days", "demo_pins", "demo_days", "bio_pins", "bio_days"]:
        panel[c] = panel[c].fillna(0).astype("int64")

    panel = panel.sort_values(keys).reset_index(drop=True)
    return panel
