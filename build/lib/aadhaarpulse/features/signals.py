from __future__ import annotations

import numpy as np
import pandas as pd


def add_signals(panel: pd.DataFrame) -> pd.DataFrame:
    """Derive governance signals from enrolments/updates.

    Outputs are proxies—because we do not use external datasets in hackathon scope.
    """

    df = panel.copy().sort_values(["state", "district", "month"]).reset_index(drop=True)

    # Migration proxy: address/mobile driven demand approximated by update intensity.
    # We don't have breakdown; use demo_total as mobility signal.
    df["migration_signal"] = np.log1p(df["demo_total"]) * (1 + df.groupby(["state", "district"])["demo_total"].pct_change().fillna(0).clip(-1, 3))

    # Urbanisation proxy: high and rising 18+ enrolments.
    df["urbanisation_signal"] = np.log1p(df["enrol_age_18p"]) * (1 + df.groupby(["state", "district"])["enrol_age_18p"].pct_change().fillna(0).clip(-1, 3))

    # Ageing proxy: high biometric pressure relative to enrolment can suggest ageing refresh.
    df["ageing_signal"] = (df["bio_total"] + 1) / (df["enrol_total"] + 1)

    # Inclusion proxy: share of child enrolments (0-5) indicates early-life inclusion coverage.
    df["inclusion_signal"] = (df["enrol_age_0_5"] + 1) / (df["enrol_total"] + 1)

    # Infrastructure stress proxy: combined load per active PIN footprint.
    df["load_per_pin"] = (df["enrol_total"] + df["demo_total"] + df["bio_total"]) / (df[["enrol_pins", "demo_pins", "bio_pins"]].max(axis=1).replace(0, np.nan))
    df["load_per_pin"] = df["load_per_pin"].fillna(0.0)

    return df
