from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


def _must_exist(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return path


def _find_project_root() -> Path:
    """Best-effort project root detection.

    Streamlit may be launched from different working directories (e.g., workspace root),
    and when installed editable, __file__ can resolve under site-packages.

    Strategy:
    1) Walk upwards from CWD searching for pyproject.toml (repo root)
    2) Walk upwards from this source file for pyproject.toml
    3) Fall back to CWD
    """

    # Common workspace layout: the repo is a child folder named 'aadhaarpulse'
    # under the workspace root.
    cwd = Path.cwd()
    candidate = cwd / "aadhaarpulse"
    if (candidate / "pyproject.toml").exists():
        return candidate

    for start in [cwd, Path(__file__).resolve()]:
        cur = start if start.is_dir() else start.parent
        for parent in [cur] + list(cur.parents):
            if (parent / "pyproject.toml").exists():
                return parent
    return Path.cwd()


@st.cache_data(show_spinner=False)
def load_panel(parquet_path: str) -> pd.DataFrame:
    return pd.read_parquet(parquet_path)


@st.cache_data(show_spinner=False)
def load_csv(csv_path: str) -> pd.DataFrame:
    return pd.read_csv(csv_path)


def main() -> None:
    st.set_page_config(page_title="AadhaarPulse Dashboard", layout="wide")

    st.title("AadhaarPulse – India’s Identity & Service Intelligence Engine")
    st.caption(
        "District-level intelligence from UIDAI enrolment + demographic update + biometric update datasets."
    )

    root_default = str(_find_project_root())
    with st.sidebar:
        st.header("Data sources")
        project_root = Path(st.text_input("Project root", value=root_default))

        panel_path = project_root / "data" / "processed" / "district_month_panel.parquet"
        tables_dir = project_root / "reports" / "tables"

        st.write("Detected paths:")
        st.code(str(panel_path))
        st.code(str(tables_dir))

        if st.button("Reload data"):
            st.cache_data.clear()

        st.divider()
        disaster_mode = st.toggle(
            "🚨 Disaster Mode",
            value=False,
            help="Lowers stress thresholds (Critical: 80→60) to simulate crisis sensitivity (e.g., Pandemic/Flood)."
        )

    panel = load_panel(str(_must_exist(panel_path)))

    # Normalize types
    panel["month"] = pd.to_datetime(panel["month"], errors="coerce")

    latest_month = panel["month"].max()
    st.success(f"Loaded {len(panel):,} district-month rows. Latest month: {latest_month.date()}")

    # ----------------------------
    # KPI strip (national overview)
    # ----------------------------
    latest_all = panel.loc[panel["month"] == latest_month].copy()
    # Safety: if ASSI columns are missing, keep dashboard usable
    has_assi = "ASSI_0_100" in latest_all.columns
    has_anom = "anomaly_flag" in latest_all.columns

    total_districts = latest_all[["state", "district"]].drop_duplicates().shape[0]
    critical_cut = 60.0 if disaster_mode else 80.0
    high_cut = 40.0 if disaster_mode else 60.0

    if has_assi:
        mean_assi = float(latest_all["ASSI_0_100"].mean())
        critical = int((latest_all["ASSI_0_100"] >= critical_cut).sum())
        high = int((latest_all["ASSI_0_100"] >= high_cut).sum())
    else:
        mean_assi, critical, high = 0.0, 0, 0

    if has_anom:
        anomalies = int(latest_all["anomaly_flag"].fillna(False).sum())
    else:
        anomalies = 0

    nat_enrol = int(latest_all.get("enrol_total", pd.Series([0])).sum())
    nat_demo = int(latest_all.get("demo_total", pd.Series([0])).sum())
    nat_bio = int(latest_all.get("bio_total", pd.Series([0])).sum())
    nat_updates = nat_demo + nat_bio
    updates_per_enrol = (nat_updates + 1) / (nat_enrol + 1)

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Districts (latest)", f"{total_districts:,}")
    k2.metric("Mean ASSI", f"{mean_assi:.1f}" if has_assi else "n/a")
    k3.metric("High stress (ASSI≥60)", f"{high:,}" if has_assi else "n/a")
    k4.metric("Critical (ASSI≥80)", f"{critical:,}" if has_assi else "n/a")
    k5.metric("Anomaly flags", f"{anomalies:,}" if has_anom else "n/a")
    k6.metric("Updates / Enrol", f"{updates_per_enrol:.2f}")

    with st.expander("What these KPIs mean", expanded=False):
        st.markdown(
            "- **Mean ASSI**: national average stress score (0–100).\n"
            "- **High/Critical**: count of district-months crossing thresholds (watchlist vs urgent).\n"
            "- **Anomaly flags**: districts with sudden spikes/drops (early warning).\n"
            "- **Updates/Enrol**: operational load intensity proxy; higher implies more updates per new onboarding.\n"
        )

    # Filters
    colA, colB, colC = st.columns([2, 2, 2])
    with colA:
        state = st.selectbox("State", options=["(All)"] + sorted(panel["state"].dropna().unique().tolist()))
    with colB:
        month_min = panel["month"].min()
        month_max = panel["month"].max()
        month_range = st.slider(
            "Month range",
            min_value=month_min.to_pydatetime(),
            max_value=month_max.to_pydatetime(),
            value=(month_min.to_pydatetime(), month_max.to_pydatetime()),
        )
    with colC:
        top_n = st.slider("Top districts", min_value=10, max_value=200, value=50, step=10)

    df = panel.copy()
    if state != "(All)":
        df = df[df["state"] == state]

    df = df[(df["month"] >= pd.Timestamp(month_range[0])) & (df["month"] <= pd.Timestamp(month_range[1]))]

    # Insight row: stress distribution + top movers
    c1, c2 = st.columns([1.2, 1])
    with c1:
        if has_assi:
            st.markdown("### Stress distribution (latest month)")
            fig = px.histogram(latest_all, x="ASSI_0_100", nbins=20)
            fig.update_layout(height=260, xaxis_title="ASSI (0–100)", yaxis_title="# Districts")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ASSI columns not found; run the pipeline to compute ASSI.")

    with c2:
        st.markdown("### Top movers (month-over-month)")
        if "ASSI_0_100" in panel.columns:
            tmp = panel.sort_values(["state", "district", "month"]).copy()
            tmp["assi_change"] = tmp.groupby(["state", "district"])["ASSI_0_100"].diff()
            movers = (
                tmp.loc[tmp["month"] == latest_month]
                .sort_values("assi_change", ascending=False)
                .head(10)[["state", "district", "ASSI_0_100", "assi_change", "enrol_total", "demo_total", "bio_total"]]
            )
            st.dataframe(movers, use_container_width=True, height=260)
        else:
            st.info("ASSI changes unavailable.")

    st.divider()

    # Tabs
    tab1, tab2, tab_intervention, tab3, tab4, tab5 = st.tabs(
        ["Stress hotspots", "Trends", "Intervention Planner", "Forecasts", "What-if simulator", "Downloads"]
    )

    with tab1:
        st.subheader("ASSI hotspots (latest month)")
        latest = df[df["month"] == df["month"].max()].copy()
        latest = latest.sort_values("ASSI_0_100", ascending=False)
        show_cols = [
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
        show_cols = [c for c in show_cols if c in latest.columns]
        st.dataframe(latest.head(top_n)[show_cols], use_container_width=True)

        # Driver snapshot: which component dominates for top districts
        if {"enrol_total", "demo_total", "bio_total"}.issubset(set(latest.columns)):
            st.markdown("### Stress drivers (top districts)")
            td = latest.head(min(top_n, 100)).copy()
            td["updates_total"] = td["demo_total"] + td["bio_total"]
            melt = td.melt(
                id_vars=["state", "district"],
                value_vars=["enrol_total", "updates_total", "bio_total"],
                var_name="driver",
                value_name="volume",
            )
            fig = px.bar(
                melt,
                x="district",
                y="volume",
                color="driver",
                title="Volumes behind stress (top set)",
            )
            fig.update_layout(height=420, xaxis_title="District", yaxis_title="Volume")
            st.plotly_chart(fig, use_container_width=True)

        # Map-style plot without shapefiles: state-level bubble of mean stress
        st.markdown("### State summary (mean ASSI)")
        state_summary = (
            latest.groupby("state", as_index=False)
            .agg(mean_assi=("ASSI_0_100", "mean"), districts=("district", "nunique"))
            .sort_values("mean_assi", ascending=False)
        )
        fig = px.bar(state_summary.head(20), x="state", y="mean_assi", hover_data=["districts"]) 
        fig.update_layout(height=380, xaxis_title="State", yaxis_title="Mean ASSI (0–100)")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("National / state trends")

        gcols = ["month"]
        trend = (
            df.groupby(gcols, as_index=False)[["enrol_total", "demo_total", "bio_total"]]
            .sum()
            .sort_values("month")
        )
        fig = px.line(
            trend,
            x="month",
            y=["enrol_total", "demo_total", "bio_total"],
            markers=True,
            title="Monthly totals",
        )
        fig.update_layout(height=420, yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Anomaly watchlist")
        if "anomaly_flag" in df.columns:
            anomalies = df[df["anomaly_flag"]].sort_values(["month", "ASSI_0_100"], ascending=[False, False])
            st.dataframe(anomalies.head(200)[show_cols], use_container_width=True)
        else:
            st.info("No anomaly_flag column found in panel.")

        st.markdown("### Early-warning: forecasted surge candidates")
        forecast_path = tables_dir / "district_forecast_12m.csv"
        if forecast_path.exists() and has_assi:
            fc = load_csv(str(forecast_path))
            fc["month"] = pd.to_datetime(fc["month"], errors="coerce")
            # Compare first forecast month to last observed month (district-level)
            first_fc_month = fc["month"].min()
            base = latest_all[["state", "district", "enrol_total", "demo_total", "bio_total", "ASSI_0_100"]].copy()
            f1 = fc.loc[fc["month"] == first_fc_month].copy()
            f1 = f1.rename(
                columns={
                    "pred_enrol_total": "enrol_fc1",
                    "pred_demo_total": "demo_fc1",
                    "pred_bio_total": "bio_fc1",
                }
            )
            m = base.merge(f1[["state", "district", "enrol_fc1", "demo_fc1", "bio_fc1"]], on=["state", "district"], how="inner")
            m["updates_now"] = m["demo_total"] + m["bio_total"]
            m["updates_fc1"] = m["demo_fc1"] + m["bio_fc1"]
            m["updates_growth_fc1"] = (m["updates_fc1"] + 1) / (m["updates_now"] + 1) - 1
            alerts = m.sort_values(["updates_growth_fc1", "ASSI_0_100"], ascending=False).head(50)
            st.dataframe(
                alerts[[
                    "state",
                    "district",
                    "ASSI_0_100",
                    "updates_growth_fc1",
                    "enrol_total",
                    "updates_now",
                    "updates_fc1",
                ]],
                use_container_width=True,
            )
        else:
            st.caption("Forecast alerts appear once `district_forecast_12m.csv` exists.")

    with tab_intervention:
        st.subheader("Intervention Planner (Immediate Action)")

        planner_df = latest_all.copy()

        if has_assi:
            # ---------------------------------------------------------
            # 1. Calculate Intervention Priority Score
            # Formula: ASSI + (Migration * 20) + (Anomaly * 15)
            # ---------------------------------------------------------
            # Start with existing ASSI
            planner_df["priority_score"] = planner_df["ASSI_0_100"]

            # Add weight for migration if available
            if "migration_signal" in planner_df.columns:
                # If boolean or 0/1, multiply by 20. If continuous 0-100, scale appropriately.
                # Assuming 1/True for signal.
                planner_df["priority_score"] += planner_df["migration_signal"].apply(lambda x: 20 if x else 0)

            # Add weight for anomalies
            if "anomaly_flag" in planner_df.columns:
                planner_df["priority_score"] += planner_df["anomaly_flag"].fillna(False).apply(lambda x: 15 if x else 0)

            # ---------------------------------------------------------
            # 2. Top Actionable Districts
            # ---------------------------------------------------------
            st.markdown("#### 🚨 Top 10 Districts Requiring Immediate Intervention")
            st.caption(
                "Ranked by **Intervention Priority Score**: High ASSI + Migration Risk + Recent Anomalies."
            )

            top_action = planner_df.sort_values("priority_score", ascending=False).head(10)
            disp_cols = ["state", "district", "priority_score", "ASSI_0_100", "enrol_total", "demo_total"]
            if "migration_signal" in planner_df.columns:
                disp_cols.append("migration_signal")

            st.dataframe(
                top_action[disp_cols].style.background_gradient(subset=["priority_score"], cmap="Reds"),
                use_container_width=True,
            )

            # ---------------------------------------------------------
            # 3. Resource Re-allocation Advisor
            # ---------------------------------------------------------
            st.divider()
            st.markdown("#### ⚖️ Resource Re-allocation Advisor")
            st.caption(
                "Optimization Engine: Shift kits/staff from **Surplus (Low Stress)** to **Deficit (Critical)** districts within the same state."
            )

            st_plan_list = sorted(planner_df["state"].dropna().unique())
            selected_state_plan = st.selectbox("Select State to Optimize", options=st_plan_list, key="plan_st")

            if selected_state_plan:
                state_data = planner_df[planner_df["state"] == selected_state_plan]

                col_deficit, col_surplus = st.columns(2)

                with col_deficit:
                    st.error("🔴 DEFICIT (Stress > 70)")
                    st.caption("Move resources TO here")
                    deficit_df = (
                        state_data[state_data["ASSI_0_100"] >= 70]
                        .sort_values("ASSI_0_100", ascending=False)
                        .reset_index(drop=True)
                    )
                    if not deficit_df.empty:
                        st.dataframe(deficit_df[["district", "ASSI_0_100"]], use_container_width=True)
                    else:
                        st.info("No critical districts in this state.")

                with col_surplus:
                    st.success("🟢 SURPLUS (Stress < 40)")
                    st.caption("Move resources FROM here")
                    surplus_df = (
                        state_data[state_data["ASSI_0_100"] <= 40]
                        .sort_values("ASSI_0_100", ascending=True)
                        .reset_index(drop=True)
                    )
                    if not surplus_df.empty:
                        st.dataframe(surplus_df[["district", "ASSI_0_100"]], use_container_width=True)
                    else:
                        st.warning("No low-stress districts available to draw from.")

        else:
            st.warning("Intervention Planner requires ASSI computation. Please run the pipeline.")

    with tab3:
        st.subheader("Forecasts (next 12 months)")
        forecast_path = tables_dir / "district_forecast_12m.csv"
        if forecast_path.exists():
            fc = load_csv(str(forecast_path))
            fc["month"] = pd.to_datetime(fc["month"], errors="coerce")

            # Pick a district
            options = (
                df[["state", "district"]].drop_duplicates().sort_values(["state", "district"]).values.tolist()
            )
            pick = st.selectbox("District", options=options, format_func=lambda x: f"{x[0]} – {x[1]}")
            st_state, st_dist = pick

            hist = panel[(panel["state"] == st_state) & (panel["district"] == st_dist)].copy()
            hist = hist.sort_values("month")
            fcd = fc[(fc["state"] == st_state) & (fc["district"] == st_dist)].copy().sort_values("month")

            m = pd.concat(
                [
                    hist[["month", "enrol_total", "demo_total", "bio_total"]].assign(kind="history"),
                    fcd[["month", "pred_enrol_total", "pred_demo_total", "pred_bio_total"]]
                    .rename(
                        columns={
                            "pred_enrol_total": "enrol_total",
                            "pred_demo_total": "demo_total",
                            "pred_bio_total": "bio_total",
                        }
                    )
                    .assign(kind="forecast"),
                ],
                ignore_index=True,
            )

            fig = px.line(m, x="month", y=["enrol_total", "demo_total", "bio_total"], color="kind", markers=True)
            fig.update_layout(height=420, yaxis_title="Volume")
            st.plotly_chart(fig, use_container_width=True)

            metrics_path = tables_dir / "forecast_metrics.csv"
            if metrics_path.exists():
                st.markdown("### Forecast baseline quality")
                st.dataframe(load_csv(str(metrics_path)), use_container_width=True)
        else:
            st.warning(f"Missing forecast file: {forecast_path}")

    with tab4:
        st.subheader("What-if policy simulator")
        whatif_path = tables_dir / "what_if_top200.csv"
        if whatif_path.exists():
            w = load_csv(str(whatif_path))
            w["month"] = pd.to_datetime(w["month"], errors="coerce")
            st.dataframe(w.head(200), use_container_width=True)

            st.markdown("### Average stress reduction in top-200")
            if {"ASSI", "assi_after_centers", "assi_after_bio_drive"}.issubset(set(w.columns)):
                summary = pd.DataFrame(
                    {
                        "Scenario": ["Baseline", "Add centres", "Biometric drive"],
                        "Mean ASSI": [
                            w["ASSI"].mean(),
                            w["assi_after_centers"].mean(),
                            w["assi_after_bio_drive"].mean(),
                        ],
                    }
                )
                fig = px.bar(summary, x="Scenario", y="Mean ASSI")
                fig.update_layout(height=360)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"Missing what-if file: {whatif_path}")

    with tab5:
        st.subheader("Download outputs")
        st.caption("These files are generated by the pipeline and can be attached directly to PPT/PDF.")

        cA, cB, cC = st.columns(3)
        with cA:
            st.markdown("**Latest leaderboard**")
            lb_path = tables_dir / "district_assi_top100_latest.csv"
            if lb_path.exists():
                st.download_button(
                    "Download district_assi_top100_latest.csv",
                    data=lb_path.read_bytes(),
                    file_name="district_assi_top100_latest.csv",
                    mime="text/csv",
                )
        with cB:
            st.markdown("**Forecasts**")
            fc_path = tables_dir / "district_forecast_12m.csv"
            if fc_path.exists():
                st.download_button(
                    "Download district_forecast_12m.csv",
                    data=fc_path.read_bytes(),
                    file_name="district_forecast_12m.csv",
                    mime="text/csv",
                )
        with cC:
            st.markdown("**What-if scenarios**")
            wi_path = tables_dir / "what_if_top200.csv"
            if wi_path.exists():
                st.download_button(
                    "Download what_if_top200.csv",
                    data=wi_path.read_bytes(),
                    file_name="what_if_top200.csv",
                    mime="text/csv",
                )


if __name__ == "__main__":
    main()
