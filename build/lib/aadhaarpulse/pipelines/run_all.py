from __future__ import annotations

from pathlib import Path

import pandas as pd

from aadhaarpulse.config import DataPaths, OutputPaths
from aadhaarpulse.features.assi import assi_formula_markdown, compute_assi
from aadhaarpulse.features.signals import add_signals
from aadhaarpulse.models.forecasting import fit_predict_next_months
from aadhaarpulse.pipelines.cleaning import (
    clean_biometric,
    clean_demographic,
    clean_enrolment,
    to_district_month,
)
from aadhaarpulse.pipelines.analysis import add_growth_and_anomalies
from aadhaarpulse.pipelines.io import load_biometric, load_demographic, load_enrolment
from aadhaarpulse.pipelines.panel import build_panel
from aadhaarpulse.simulator.what_if import Scenario, recommend_targets, simulate_biometric_drive, simulate_centers


def run_all(*, data_root: Path, project_root: Path) -> None:
    data = DataPaths(data_root=data_root)
    out = OutputPaths(project_root=project_root)
    out.interim_dir.mkdir(parents=True, exist_ok=True)
    out.processed_dir.mkdir(parents=True, exist_ok=True)
    out.tables_dir.mkdir(parents=True, exist_ok=True)
    out.figures_dir.mkdir(parents=True, exist_ok=True)

    enrol_raw = load_enrolment(data.enrolment_dir)
    demo_raw = load_demographic(data.demographic_dir)
    bio_raw = load_biometric(data.biometric_dir)

    enrol = to_district_month(clean_enrolment(enrol_raw))
    demo = to_district_month(clean_demographic(demo_raw))
    bio = to_district_month(clean_biometric(bio_raw))

    panel = build_panel(enrol, demo, bio)

    # Signals, anomalies, and ASSI
    panel = add_signals(panel)
    panel = add_growth_and_anomalies(panel)
    panel = compute_assi(panel)

    # Persist curated panel
    panel_path = out.processed_dir / "district_month_panel.parquet"
    panel.to_parquet(panel_path, index=False)

    # Forecasts
    forecast, metrics = fit_predict_next_months(panel[["state", "district", "month", "enrol_total", "demo_total", "bio_total"]], horizon_months=12)
    forecast.to_csv(out.tables_dir / "district_forecast_12m.csv", index=False)
    pd.DataFrame({"metric": list(metrics.keys()), "value": list(metrics.values())}).to_csv(
        out.tables_dir / "forecast_metrics.csv", index=False
    )

    # What-if scenarios (top stress districts)
    top = recommend_targets(panel, top_k=200)
    top_mask = panel.index.isin(top.index)
    scenario = Scenario(center_capacity_uplift=0.20, biometric_drive_uplift=0.35)
    whatif = simulate_centers(panel, pd.Series(top_mask, index=panel.index), scenario)
    whatif = simulate_biometric_drive(whatif, pd.Series(top_mask, index=panel.index), scenario)
    whatif[["state", "district", "month", "ASSI", "assi_after_centers", "assi_after_bio_drive"]].to_csv(
        out.tables_dir / "what_if_top200.csv", index=False
    )

    # ASSI doc snippet
    (out.tables_dir / "assi_formula.md").write_text(assi_formula_markdown(), encoding="utf-8")

    # Minimal national summary table
    national = (
        panel.groupby(["month"], as_index=False)[["enrol_total", "demo_total", "bio_total"]]
        .sum()
        .sort_values("month")
    )
    national.to_csv(out.tables_dir / "national_monthly_totals.csv", index=False)

    # District stress leaderboard (latest month)
    latest_month = panel["month"].max()
    leaderboard = (
        panel.loc[panel["month"] == latest_month]
        .sort_values("ASSI", ascending=False)
        .head(100)[
            [
                "state",
                "district",
                "month",
                "ASSI_0_100",
                "enrol_total",
                "demo_total",
                "bio_total",
                "migration_signal",
                "urbanisation_signal",
                "ageing_signal",
                "inclusion_signal",
                "anomaly_flag",
            ]
        ]
    )
    leaderboard.to_csv(out.tables_dir / "district_assi_top100_latest.csv", index=False)

    # quick data health report
    health = pd.DataFrame(
        {
            "metric": [
                "enrol_rows_raw",
                "demo_rows_raw",
                "bio_rows_raw",
                "panel_rows",
                "districts",
                "states",
                "months",
            ],
            "value": [
                len(enrol_raw),
                len(demo_raw),
                len(bio_raw),
                len(panel),
                panel[["state", "district"]].drop_duplicates().shape[0],
                panel["state"].nunique(),
                panel["month"].nunique(),
            ],
        }
    )
    health.to_csv(out.tables_dir / "data_health.csv", index=False)
