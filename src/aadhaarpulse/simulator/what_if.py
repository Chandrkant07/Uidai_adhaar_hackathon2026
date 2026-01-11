from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Scenario:
    """Policy scenario knobs.

    center_capacity_uplift: Fractional uplift in service capacity for targeted districts.
    biometric_drive_uplift: Fractional uplift in biometric update throughput for targeted districts.
    """

    center_capacity_uplift: float = 0.15
    biometric_drive_uplift: float = 0.25


def simulate_centers(
    df: pd.DataFrame,
    target_mask: pd.Series,
    scenario: Scenario,
) -> pd.DataFrame:
    """What-if: adding centres in high-migration/stress districts.

    Without centre inventory or SLA data, we simulate by reducing stress via higher effective capacity.
    We assume added capacity reduces backlog proxy: updates-per-enrolment and anomaly residuals.
    """

    out = df.copy()
    uplift = scenario.center_capacity_uplift

    # Backlog proxy: friction + update load
    out["assi_after_centers"] = out["ASSI"].where(~target_mask, out["ASSI"] * (1 - 0.30 * uplift))
    return out


def simulate_biometric_drive(
    df: pd.DataFrame,
    target_mask: pd.Series,
    scenario: Scenario,
) -> pd.DataFrame:
    """What-if: biometric refresh drives in ageing/high-bio-pressure districts.

    We simulate by reducing bio pressure component (bio_per_enrol) over the next periods.
    """

    out = df.copy()
    uplift = scenario.biometric_drive_uplift
    out["assi_after_bio_drive"] = out["ASSI"].where(~target_mask, out["ASSI"] * (1 - 0.25 * uplift))
    return out


def recommend_targets(df: pd.DataFrame, top_k: int = 100) -> pd.DataFrame:
    """Return top-k district-month rows by stress score for action prioritisation."""

    cols = ["state", "district", "month", "ASSI", "ASSI_0_100", "enrol_total", "demo_total", "bio_total"]
    available = [c for c in cols if c in df.columns]
    return df.sort_values("ASSI", ascending=False).head(top_k)[available]
